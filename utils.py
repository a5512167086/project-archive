import json
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_driver():
    chrome_options = Options()
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    return webdriver.Chrome(options=chrome_options)


def wait_for_element(driver, by, selector, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, selector))
    )


def get_product_links(driver, url: str) -> List[str]:
    driver.get(url)

    link_array = []
    while True:
        try:
            # Wait for the product list to load
            wait_for_element(driver, By.ID, "layer-product-list")

            main_element = driver.find_element(By.ID, "layer-product-list")
            product_item_box = main_element.find_element(By.CLASS_NAME, "product-items")
            link_elements = product_item_box.find_elements(
                By.CLASS_NAME, "product-item-link-image"
            )

            # Extract product links
            for child in link_elements:
                href = child.get_attribute("href")
                if href:
                    link_array.append(href)

            # Locate the next page button
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


def get_product_details(driver, product_link: str) -> Dict[str, str]:
    driver.get(product_link)
    try:
        product_brand_name = wait_for_element(
            driver, By.CSS_SELECTOR, "[itemprop='brand']"
        ).text
        product_chinese_name = wait_for_element(
            driver, By.CSS_SELECTOR, "[itemprop='name']"
        ).text
        product_english_name = wait_for_element(
            driver, By.CSS_SELECTOR, "[itemprop='description']"
        ).text
        product_lowest_price = wait_for_element(driver, By.CLASS_NAME, "price").text
        product_description = wait_for_element(
            driver, By.CSS_SELECTOR, ".product.attribute.description"
        ).text
        product_instruction = wait_for_element(
            driver, By.CLASS_NAME, "Instructions_for_use"
        ).get_attribute("innerText")
        product_ingredient = wait_for_element(
            driver, By.CLASS_NAME, "Main_ingredients"
        ).get_attribute("innerText")

        product_image_box = wait_for_element(
            driver, By.CSS_SELECTOR, ".fotorama__stage__shaft.fotorama__grab"
        )
        product_images = product_image_box.find_elements(By.TAG_NAME, "img")
        product_first_two_images = [
            img.get_attribute("src") or img.get_attribute("data-src")
            for img in product_images[:2]
        ]

        return {
            "product_brand_name": product_brand_name.strip(),
            "product_chinese_name": product_chinese_name.strip(),
            "product_english_name": product_english_name.strip(),
            "product_lowest_price": product_lowest_price.strip(),
            "product_description": re.sub(r"\s+", " ", product_description).strip(),
            "product_instruction": product_instruction.strip(),
            "product_ingredient": product_ingredient.strip(),
            "product_link": product_link,
            "product_images": product_first_two_images,
        }
    except NoSuchElementException:
        logger.warning(f"Missing element in {product_link}")
        return {}


def get_product_by_url(url: str):
    driver = create_driver()
    try:
        start_time = time.time()

        # Get product links
        logger.info("Fetching product links...")
        product_links = get_product_links(driver, url)
        logger.info(f"Found {len(product_links)} product links.")

        # Concurrently fetch product details
        product_array = []
        logger.info("Fetching product details...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(
                lambda link: get_product_details(driver, link), product_links
            )

        for product in results:
            if product:
                product_array.append(product)

        end_time = time.time()
        logger.info(f"Execution time: {end_time - start_time:.2f} seconds")
        return product_array
    finally:
        driver.quit()


def save_to_json(data: List[Dict], filename: str = "product.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logger.info(f"Data saved to {filename}")
