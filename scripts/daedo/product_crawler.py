import asyncio
import itertools
import json
import os
from urllib.parse import urljoin

from playwright.async_api import async_playwright

URL = "https://www.daedo.com/pages/taekwondo-wt"
BASE_URL = "https://www.daedo.com"
OUTPUT_FILE = "data/daedo_products.json"
MAX_CONCURRENCY = 5


def _norm(text: str | None) -> str | None:
    if not text:
        return None
    return " ".join(text.split())


# 💡 階段一核心：利用 target_id 直接穿透 DOM 抓取隱藏商品
async def scrape_products(page, target_id):
    products = []
    try:
        container_sel = f"#{target_id}" if target_id else ".page-width"
        target_selector = f"{container_sel} .card__content .card__information a"

        await page.wait_for_selector(target_selector, state="attached", timeout=5000)

        anchors = page.locator(target_selector)
        count = await anchors.count()
        seen_urls = set()

        for k in range(count):
            anchor = anchors.nth(k)
            name = _norm(await anchor.text_content())
            href = await anchor.get_attribute("href")

            if name and href:
                full_url = urljoin(BASE_URL, href)
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    products.append({"name": name, "url": full_url})
    except Exception:
        pass

    return products


# 💡 階段二核心：並發抓取單一商品詳細資訊
async def fetch_detail(context, product, sema):
    async with sema:
        page = await context.new_page()
        try:
            await page.goto(
                product["url"], wait_until="domcontentloaded", timeout=30000
            )

            # --- 抓取商品名稱 ---
            try:
                title_element = page.locator(".product__title")
                await title_element.first.wait_for(state="attached", timeout=5000)
                title_text = await title_element.first.text_content()
                product["detailed_name"] = (
                    _norm(title_text) if title_text else product["name"]
                )
            except Exception:
                product["detailed_name"] = product["name"]

            # --- 💡 新增：抓取商品價格 ---
            try:
                # 注意：CSS class 中間有空格代表是兩個 class，選擇器要用 . 連接
                price_locator = page.locator(".price-item.price-item--regular")
                if await price_locator.count() > 0:
                    # 通常取第一個就是正確價格
                    price_text = await price_locator.first.text_content()
                    product["price"] = _norm(price_text)
                else:
                    product["price"] = None
            except Exception as e:
                print(f"      ⚠️ 價格抓取發生錯誤: {e}")
                product["price"] = None

            # --- 抓取圖片 src ---
            images = []
            seen_imgs = set()
            try:
                img_elements = page.locator(".product__media-list img")
                count = await img_elements.count()
                for i in range(count):
                    src = await img_elements.nth(i).get_attribute("src")
                    if src:
                        if src.startswith("//"):
                            src = "https:" + src
                        if src not in seen_imgs:
                            seen_imgs.add(src)
                            images.append(src)
            except Exception:
                pass
            product["images"] = images

            # --- 抓取變體選項並產生排列組合 ---
            variants = []
            try:
                fieldset_locator = page.locator(".product-form__input")
                fieldset_count = await fieldset_locator.count()

                groups_options = []
                for i in range(fieldset_count):
                    options = []

                    inputs = fieldset_locator.nth(i).locator('input[type="radio"]')
                    input_count = await inputs.count()

                    if input_count > 0:
                        for j in range(input_count):
                            val = await inputs.nth(j).get_attribute("value")
                            if val:
                                options.append(val.strip())
                    else:
                        selects = fieldset_locator.nth(i).locator("select option")
                        select_count = await selects.count()
                        for j in range(select_count):
                            val = await selects.nth(j).get_attribute("value")
                            if val:
                                options.append(val.strip())

                    if options:
                        groups_options.append(options)

                if groups_options:
                    for combo in itertools.product(*groups_options):
                        variants.append(" / ".join(combo))

            except Exception as e:
                print(f"      ⚠️ 變體抓取發生錯誤: {e}")

            product["variants"] = variants

            print(
                f"   ✅ 完成詳情: {product['detailed_name'][:20]}... | 價格: {product['price']} | 圖片數: {len(images)} | 變體數: {len(variants)}"
            )

        except Exception as e:
            print(f"   ❌ 詳情失敗: {product['url']} | 錯誤: {e}")
            product["detailed_name"] = product["name"]
            product["price"] = None
            product["images"] = []
            product["variants"] = []
        finally:
            await page.close()


async def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print(f"🌍 正在前往主網頁: {URL}")
        await page.goto(URL, wait_until="networkidle", timeout=60000)

        try:
            await page.wait_for_selector(".categoryimagelink", timeout=15000)
        except Exception:
            print("⚠️ 找不到大分類元素，請確認網頁結構。")
            await browser.close()
            return

        links_locator = page.locator(".categoryimagelink")
        names_locator = page.locator(".category-page__info")

        link_count = await links_locator.count()
        name_count = await names_locator.count()

        tree_data = []

        for i in range(min(link_count, name_count)):
            href = await links_locator.nth(i).get_attribute("href")
            raw_name = await names_locator.nth(i).text_content()
            clean_name = _norm(raw_name)
            full_url = urljoin(BASE_URL, href) if href else None

            if clean_name and full_url:
                tree_data.append({
                    "category_name": clean_name,
                    "url": full_url,
                    "sub_categories": [],
                })

        print(f"🎯 成功抓取 {len(tree_data)} 個大分類！\n")

        for category in tree_data:
            main_url = category["url"]
            print(f"➡️ 正在探索分類: {category['category_name']} ({main_url})")

            try:
                await page.goto(main_url, wait_until="networkidle", timeout=30000)
                tabs_locator = page.locator(".tab button.tab-button")
                tab_count = await tabs_locator.count()

                if tab_count > 0:
                    tabs_info = []
                    for j in range(tab_count):
                        tab = tabs_locator.nth(j)
                        t_name = _norm(await tab.text_content())
                        t_target_id = await tab.get_attribute("data-tab")
                        if t_name:
                            tabs_info.append({"name": t_name, "target_id": t_target_id})

                    for t_info in tabs_info:
                        sub_products = await scrape_products(page, t_info["target_id"])
                        category["sub_categories"].append({
                            "sub_category_name": t_info["name"],
                            "products": sub_products,
                        })
                else:
                    sub_products = await scrape_products(page, None)
                    category["sub_categories"].append({
                        "sub_category_name": "All",
                        "products": sub_products,
                    })

            except Exception as e:
                print(f" ❌ 載入 {category['category_name']} 失敗: {e}")

        await page.close()

        all_products = []
        for category in tree_data:
            for sub_cat in category.get("sub_categories", []):
                for prod in sub_cat.get("products", []):
                    all_products.append(prod)

        print(f"\n🚀 第一階段完成！總共收集到 {len(all_products)} 件商品。")
        print("⚡ 準備開始並發抓取商品詳細名稱、價格與圖片...\n")

        sema = asyncio.Semaphore(MAX_CONCURRENCY)
        tasks = [fetch_detail(context, prod, sema) for prod in all_products]
        await asyncio.gather(*tasks)

        await browser.close()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(tree_data, f, ensure_ascii=False, indent=2)

    print(f"\n🎉 任務大功告成！完美樹狀結構與商品詳情已儲存至 {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())
