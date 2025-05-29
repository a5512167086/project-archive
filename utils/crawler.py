import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from constants.config import SELENIUM_HUB_URL
from utils.image import extract_text_from_image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    return webdriver.Remote(command_executor=SELENIUM_HUB_URL, options=chrome_options)


def wait_for_element(driver, by, selector, timeout=3):
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
    except TimeoutException:
        return None


def get_product_links(driver, url: str) -> List[str]:
    driver.get(url)
    link_array = []
    while True:
        try:
            wait_for_element(driver, By.ID, "layer-product-list")
            main_element = driver.find_element(By.ID, "layer-product-list")
            product_item_box = main_element.find_element(By.CLASS_NAME, "product-items")
            link_elements = product_item_box.find_elements(
                By.CLASS_NAME, "product-item-link-image"
            )

            for child in link_elements:
                href = child.get_attribute("href")
                if href:
                    link_array.append(href)

            next_page_button = driver.find_element(By.CSS_SELECTOR, ".action.next")
            next_page_href = next_page_button.get_attribute("href")
            driver.get(next_page_href)
        except NoSuchElementException:
            logger.info("No more pages.")
            break
        except TimeoutException:
            logger.warning("Page load timed out.")
            break
    return link_array


def get_product_details(link: str) -> Dict[str, str]:
    driver = create_driver()
    try:
        driver.get(link)

        def get_text_or_default(by, selector, default=""):
            element = wait_for_element(driver, by, selector)
            return element.text.strip() if element else default

        def get_attribute_or_default(by, selector, attribute, default=""):
            element = wait_for_element(driver, by, selector)
            return element.get_attribute(attribute).strip() if element else default

        product_brand_name = get_text_or_default(By.CSS_SELECTOR, "[itemprop='brand']")
        product_chinese_name = get_text_or_default(By.CSS_SELECTOR, "[itemprop='name']")
        product_english_name = get_text_or_default(
            By.CSS_SELECTOR, "[itemprop='description']"
        )
        product_lowest_price = get_text_or_default(By.CLASS_NAME, "price")
        product_description = get_text_or_default(
            By.CSS_SELECTOR, ".product.attribute.description"
        )
        product_instruction = get_attribute_or_default(
            By.CLASS_NAME, "Instructions_for_use", "innerText"
        )
        product_ingredient = get_attribute_or_default(
            By.CLASS_NAME, "Main_ingredients", "innerText"
        )
        product_image_box = wait_for_element(
            driver, By.CSS_SELECTOR, ".fotorama__stage__shaft"
        )

        product_images_with_ocr = []
        if product_image_box:
            product_images = product_image_box.find_elements(By.TAG_NAME, "img")
            for img in product_images[:2]:
                image_url = img.get_attribute("src") or img.get_attribute("data-src")
                if image_url:
                    ocr_text = extract_text_from_image(image_url)
                    product_images_with_ocr.append({
                        "url": image_url,
                        "ocr_text": ocr_text,
                    })

        return {
            "product_brand_name": product_brand_name,
            "product_chinese_name": product_chinese_name,
            "product_english_name": product_english_name,
            "product_lowest_price": product_lowest_price,
            "product_description": re.sub(r"\s+", " ", product_description).strip(),
            "product_instruction": product_instruction,
            "product_ingredient": product_ingredient,
            "product_link": link,
            "product_images": product_images_with_ocr,
        }
    finally:
        driver.quit()


def process_in_batches(
    product_links: List[str], batch_size: int, wait_between_batches: int
):
    total_links = len(product_links)
    product_array = []

    for start in range(0, total_links, batch_size):
        end = start + batch_size
        batch_links = product_links[start:end]
        logger.info(f"Processing batch: {start} to {end} (total {total_links})")

        with ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(get_product_details, batch_links)

        for product in results:
            if product:
                product_array.append(product)

        if end < total_links:
            logger.info(f"Waiting {wait_between_batches} seconds before next batch...")
            time.sleep(wait_between_batches)

    return product_array


def get_products_by_url(url: str, batch_size: int = 5, wait_between_batches: int = 20):
    start_time = time.time()
    driver = create_driver()
    try:
        logger.info("Fetching product links...")
        product_links = get_product_links(driver, url)
        logger.info(f"Found {len(product_links)} product links.")
    finally:
        driver.quit()

    logger.info("Fetching product details in batches...")
    product_array = process_in_batches(product_links, batch_size, wait_between_batches)

    end_time = time.time()
    logger.info(f"Execution time: {end_time - start_time:.2f} seconds")
    return product_array
