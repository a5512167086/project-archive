import asyncio
import json
from urllib.parse import urljoin

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

URL = "https://1010online.com.tw/"
MAX_CONCURRENCY = 5  # 同時抓取商品細節的最大並發數


# ---------- 小工具：文字正規化 ----------
def _norm(text: str | None) -> str | None:
    if text is None:
        return None
    return " ".join(text.split())


def _to_int(text: str | None) -> int | None:
    """將 '1,500' -> 1500；非數字回傳 None"""
    if not text:
        return None
    t = text.replace(",", "").strip()
    if t.isdigit():
        try:
            return int(t)
        except Exception:
            return None
    return None


def _abs_url(u: str | None) -> str | None:
    if not u:
        return None
    return urljoin(URL, u.strip())


# ---------- 進入「子分類頁」抓前 N 筆商品連結 ----------
async def fetch_subcategory_products(
    page, subcategory_url: str, limit: int = 3
) -> list[str]:
    try:
        await page.goto(subcategory_url, timeout=30000)
    except PlaywrightTimeoutError:
        print(f"❌ 子分類頁載入超時: {subcategory_url}")
        return []

    try:
        await page.wait_for_selector("a.product-item-link-image", timeout=10000)
    except PlaywrightTimeoutError:
        print(f"⚠️ 沒抓到商品連結: {subcategory_url}")
        return []

    anchors = page.locator("a.product-item-link-image")
    count = await anchors.count()
    seen: set[str] = set()
    results: list[str] = []

    for i in range(min(count, max(limit * 3, limit))):
        href = await anchors.nth(i).get_attribute("href")
        if not href:
            continue
        full = urljoin(URL, href.strip())
        if full in seen:
            continue
        seen.add(full)
        results.append(full)
        if len(results) >= limit:
            break

    print(f"✅ {subcategory_url} 抓到 {len(results)} 筆商品連結")
    return results


# ---------- 進入「商品頁」抓品牌 / 名稱 / 價格 / 描述 / 圖片(前三張) ----------
async def fetch_product_detail(browser, product_url: str) -> dict:
    page = await browser.new_page()
    try:
        print(f"  ➡️ 開始抓商品: {product_url}")
        await page.goto(product_url, timeout=30000)

        # 商品名稱
        name = None
        try:
            name = await page.locator("h1.page-title span").first.inner_text()
        except Exception:
            pass
        if not name:
            try:
                name = await page.locator(
                    '[itemtype*="Product"] [itemprop="name"]'
                ).first.inner_text()
            except Exception:
                pass
        name = _norm(name)

        # 品牌
        brand = None
        try:
            brand = await page.locator(
                '[itemprop="brand"] [itemprop="name"]'
            ).first.inner_text()
        except Exception:
            pass
        if not brand:
            try:
                brand = await page.locator('[itemprop="brand"]').first.inner_text()
            except Exception:
                pass
        if not brand:
            try:
                brand = await page.locator('[itemprop="brand"]').first.get_attribute(
                    "content"
                )
            except Exception:
                pass
        brand = _norm(brand)

        # 價格
        price = None
        try:
            price = await page.locator('[itemprop="price"]').first.get_attribute(
                "content"
            )
        except Exception:
            pass
        price = _norm(price)

        # 描述
        description = None
        try:
            description = await page.locator(
                ".product.attribute.description .value"
            ).first.inner_text()
        except Exception:
            pass
        if not description:
            try:
                description = await page.locator(
                    ".product.attribute.description"
                ).first.inner_text()
            except Exception:
                pass
        description = _norm(description)

        # 圖片（fotorama）— 只取前三張
        images_set: set[str] = set()
        try:
            imgs = page.locator("div.fotorama__stage img.fotorama__img")
            cnt = await imgs.count()
            for i in range(cnt):
                node = imgs.nth(i)
                # 依序嘗試 src, data-src, data-zoom-image
                src = await node.get_attribute("src")
                if not src:
                    src = await node.get_attribute("data-src")
                if not src:
                    src = await node.get_attribute("data-zoom-image")
                src = _abs_url(src)
                if src:
                    images_set.add(src)
        except Exception:
            pass

        images = sorted(images_set)[:3]  # ⭐ 只保留前三張

        print(
            f"  ✅ 商品完成: {name} | 品牌={brand} | 價格={price} | 圖片數={len(images)}"
        )
        return {
            "url": product_url,
            "brand": brand,
            "name": name,
            "price": price,
            "description": description,
            "images": images,  # ⭐ 最多 3 張
        }
    except Exception as e:
        print(f"  ❌ 商品抓取失敗: {product_url} | {e}")
        return {
            "url": product_url,
            "brand": None,
            "name": None,
            "price": None,
            "description": None,
            "images": [],
        }
    finally:
        await page.close()


# ---------- 受 Semaphore 限制的包裝 ----------
async def fetch_product_detail_bounded(
    sema: asyncio.Semaphore, browser, url: str
) -> dict:
    async with sema:
        return await fetch_product_detail(browser, url)


# ---------- 抓主/子分類 + sample links + 商品細節（併發版） ----------
async def get_categories_and_sample_products_with_details():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(URL)
        await page.wait_for_selector("ul.aw-megamenu > li.level-top.level0")

        top_items = page.locator("ul.aw-megamenu > li.level-top.level0")
        sema = asyncio.Semaphore(MAX_CONCURRENCY)

        # 全站品牌彙整（唯一集合）
        brand_set: set[str] = set()

        # 分層資料結構：categories -> main -> sub -> products
        categories: list[dict] = []

        for i in range(5, 8):
            li = top_items.nth(i)
            main_name = _norm(await li.locator("span.text").first.inner_text())
            print(f"\n=== 主分類: {main_name} ===")

            await li.hover()
            await li.locator(":scope > ul.level0.submenu").wait_for()

            ul = li.locator(':scope ul.level1.submenu[data-parent="產品類型"]')
            exists = await ul.count() > 0

            sub_items: list[dict] = []
            if exists:
                a_nodes = ul.locator("li.level2 > a.label")
                cnt = await a_nodes.count()
                for k in range(cnt):
                    a = a_nodes.nth(k)
                    text = _norm(await a.locator("span.text").inner_text())
                    href = await a.get_attribute("href")
                    href = _abs_url(href) if href else None

                    print(f"-- 子分類: {text} ({href}) --")

                    products: list[dict] = []
                    if href:
                        # 取樣商品連結
                        sample_links = await fetch_subcategory_products(
                            page, href, limit=3
                        )
                        # 併發抓商品細節
                        tasks = [
                            asyncio.create_task(
                                fetch_product_detail_bounded(sema, browser, link)
                            )
                            for link in sample_links
                        ]
                        sample_products = await asyncio.gather(*tasks)

                        # 正規化為最終輸出格式；蒐集品牌
                        for prod in sample_products:
                            prod_item = {
                                "brand": prod.get("brand"),
                                "name": prod.get("name"),
                                "price": _to_int(prod.get("price")),
                                "url": prod.get("url"),
                                "description": prod.get("description"),
                                "images": prod.get("images") or [],
                            }
                            if prod_item["name"]:
                                products.append(prod_item)
                            if prod_item["brand"]:
                                brand_set.add(prod_item["brand"])

                    sub_items.append({
                        "name": text,
                        "href": href,
                        "products": products,
                    })

            categories.append({
                "main_category": main_name,
                "group": "產品類型",
                "sub_categories": sub_items,
            })

        # ---- 寫檔：products_YYYYMMDD_HHMMSS.json ----
        outfile = "products.json"
        payload = {
            "crawl_meta": {
                "source": URL,
            },
            "brands": sorted(brand_set),
            "categories": categories,
        }
        with open(outfile, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        print("\n🎉 全部完成")
        print(f"📄 已輸出 JSON 檔案：{outfile}")
        await browser.close()


# ---------- 執行 ----------
if __name__ == "__main__":
    asyncio.run(get_categories_and_sample_products_with_details())
