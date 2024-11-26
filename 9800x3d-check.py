import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from discord_webhook import DiscordWebhook

# --------------------- Configuration ---------------------

# Discord webhook URL (Replace with your actual webhook URL)
DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/your_url'

# List of items to monitor
items_to_monitor = [
    {
        'url': 'https://www.pc-koubou.jp/products/detail.php?product_id=1107785',
        'class_name': 'btn-ggreen fs14 pl25 pr25 sold-out',
        'target_text': '受付終了'
    },
    {
        'url': 'https://www.ark-pc.co.jp/i/10240267/',
        'class_name': 'stat-panel-101',
        'target_text': '在庫なし'
    },
    {
        'url': 'https://www.dospara.co.jp/SBR1299/IC516296.html',
        'class_name': 'tx-delivery-date-class-disp_elm p-product-show-detail__delivery-label--blue',
        'target_text': '在庫なし'
    },
    {
        'url': 'https://shop.tsukumo.co.jp/goods/0730143315289/',
        'class_name': 'stock-status limited',
        'target_text': '在庫なし'
    },
    {
        'url': 'https://ocworks.com/products/amd-ryzen7-9800x3d-box?srsltid=AfmBOooYQEG6AXdyTPiwj1LiPqDl_KTdpBeyk5O2U5djEL83l_tkARxa',
        'class_name': 'product-form__add-button button button--disabled',
        'target_text': '品切れ中'
    },
    {
        'url': 'https://www.biccamera.com/bc/item/13640117/',
        'class_name': 'bcs_red',
        'target_text': 'この商品は在庫がなくなりました。'
    },
    {
        'url': 'https://shop.applied-net.co.jp/shopdetail/000000434726/',
        'class_name': 'nostockBtn',
        'target_text': '品切れ'
    },
    {
        'url': 'https://www.qd-store.jp/c-item-detail?ic=0730143315289',
        'class_name': 'cart_button soldout',
        'target_text': 'SOLD OUT'
    },
    {
        'url': 'https://www.suruga-ya.jp/product/detail/145273281',
        'class_name': 'mgnB5 out-of-stock-text',
        'target_text': '申し訳ございません。品切れ中です。'
    },
    {
        'url': 'https://www.sofmap.com/product_detail.aspx?sku=101358000',
        'class_name': 'ic stock closed',
        'target_text': '在庫切れ'
    },
    {
        'url': 'https://www.kojima.net/ec/prod_detail.html?prod=0730143315289',
        'class_name': 'deliv opt-large',
        'target_text': 'ネット在庫完売'
    },
    {
        'url': 'https://joshinweb.jp/srhzs.html?KEYWORD=&KEY=ZS_ALL&KEY_M=ALL&QS=&QK=Ryzen+7+9800x3d&category_id=&REQUEST_CODE=1',
        'class_name': 'soldout',
        'target_text': '完売いたしました'
    }

]

# Logging Configuration
logging.basicConfig(
    filename='availability_checker.log',
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s'
)

# --------------------------------------------------------

def send_discord_notification(message):
    """
    Sends a notification message to the specified Discord webhook.
    """
    webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL, content=message)
    try:
        response = webhook.execute()
        if response.status_code in [200, 204]:
            logging.info(f"Notification sent: {message}")
        else:
            logging.error(f"Failed to send notification. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Exception occurred while sending notification: {e}")

def check_availability(driver, item):
    """
    Checks the availability of an item on a webpage.
    Notifies via Discord if the item is available or if the class is not found.
    """
    url = item['url']
    class_name = item['class_name']
    target_text = item['target_text'].lower()  # Case-insensitive comparison

    logging.info(f"Checking URL: {url}")

    try:
        driver.get(url)
        # Dynamic wait instead of fixed sleep
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        try:
            # Wait up to 10 seconds for the class to be present
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, class_name))
            )
            elements = driver.find_elements(By.CLASS_NAME, class_name)
            if not elements:
                # Class exists in the DOM but no elements found
                logging.warning(f"No elements found with class '{class_name}' on {url}.")
                message = f"⚠️ **Class Not Found Warning!**\nThe class '{class_name}' was found but contains no elements on {url}. This might indicate a layout change."
                send_discord_notification(message)
                return
        except TimeoutException:
            # Class not found within the timeout period
            logging.error(f"Class '{class_name}' not found on {url}. Possible layout change.")
            message = f"🚨 **Class Not Found Alert!**\nThe class '{class_name}' was not found on {url}. This likely means the website layout has changed."
            send_discord_notification(message)
            return

        # Proceed to check for target text within found elements
        text_found = False
        for element in elements:
            if target_text in element.text.lower():
                text_found = True
                logging.info(f"Found '{target_text}' in class '{class_name}' on {url}.")
                break

        if not text_found:
            # If target text not found, send notification indicating item is available
            message = f"🔔 **Ryzen 7 9800X3D Available!**\n{url}"
            send_discord_notification(message)
        else:
            logging.info(f"Ryzen 7 9800X3D is still unavailable on {url}.")

    except TimeoutException:
        logging.error(f"Timeout while loading {url}.")
        message = f"⏰ **Timeout Alert!**\nThe page at {url} took too long to load."
        send_discord_notification(message)
    except Exception as e:
        logging.error(f"An error occurred while checking {url}: {e}")
        message = f"❌ **Error Alert!**\nAn error occurred while checking {url}: {e}"
        send_discord_notification(message)

def main():
    # Set up Selenium WebDriver in headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems

    # Initialize the WebDriver (Ensure the chromedriver is in PATH)
    driver = webdriver.Chrome(options=chrome_options)

    try:
        for item in items_to_monitor:
            check_availability(driver, item)
            # Optional: Add delay between requests to avoid being blocked
            time.sleep(300)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
