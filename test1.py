from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
import re
import time
import pandas as pd
# WhatsApp Business number for Treebo Club Support
TREEBO_NAME = "Treebo Club Support"
TREEBO_NUMBER = "+91 95130 00497"
# Persist session
CHROME_USER_DATA_DIR = os.path.join(os.getcwd(), "whatsapp_session")
os.makedirs(CHROME_USER_DATA_DIR, exist_ok=True)
def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={CHROME_USER_DATA_DIR}")
    prefs = {
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
        "profile.default_content_setting_values.automatic_downloads": 1,
    }
    options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver
def login_whatsapp(driver):
    driver.get("https://web.whatsapp.com")
    print("Opening WhatsApp Web...")
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "side"))
    )
    print("Logged into WhatsApp Web")
def open_chat(driver, name_or_number):
    print(f"Searching for chat: {name_or_number}")
    search_box = WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
    )
    search_box.click()
    time.sleep(0.5)
    search_box.send_keys(Keys.CONTROL + "a")
    search_box.send_keys(Keys.BACKSPACE)
    time.sleep(0.5)
    search_box.send_keys(name_or_number)
    time.sleep(0.5)
    try:
        chat = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f'//span[@title="{name_or_number}"]'))
        )
        chat.click()
        print("Chat opened successfully")
        return True
    except:
        print("Chat not found")
        return False
    
def clear_chat(driver):
    try:
        menu_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//span[@data-icon="menu"]'))
        )
        menu_button.click()
        time.sleep(1)
        clear_chat_option = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "Clear chat")]'))
        )
        clear_chat_option.click()
        time.sleep(1)
        clear_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "Clear")]'))
        )
        clear_button.click()
        time.sleep(2)
        print("Chat cleared successfully")
    except Exception as e:
        print(f"Error clearing chat: {str(e)}")

def send_message(driver, message):
    print(f"Sending message: {message}")
    msg_box = WebDriverWait(driver, 2).until(
        EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
    )
    msg_box.send_keys(message + Keys.ENTER)
    print("Message sent")
def get_latest_response(driver):
    try:
        # Find only incoming messages (from the bot)
        message_blocks = driver.find_elements(By.XPATH, '//div[contains(@class, "message-in")]')
        all_texts = []
        for block in message_blocks:
            text_elements = block.find_elements(By.XPATH, './/span | .//div')
            for elem in text_elements:
                text = elem.text.strip()
                if text:
                    all_texts.append(text)
        if all_texts:
            latest = all_texts[-1]
            print(f"Latest bot message: {latest}")
            return latest
        else:
            return None
    except Exception as e:
        print(f"Error retrieving bot messages: {e}")
        return None
def wait_for_followup_message(driver, timeout=5):
    print("Waiting for follow-up response...")
    end_time = time.time() + timeout
    last_text = get_latest_response(driver)
    while time.time() < end_time:
        new_text = get_latest_response(driver)
        if new_text and new_text != last_text:
            print(f"New message received: {new_text}")
            return new_text
        time.sleep(0.1)
    return None
def send_message_and_wait(driver, message, timeout=2):
    send_message(driver, message)
    response = wait_for_followup_message(driver, timeout=timeout)
    return response
def click_pdf_download_icon(driver, booking_id):
    print(f"Downloading PDF for Booking ID: {booking_id}")
    download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    def get_pdf_files():
        return set(f for f in os.listdir(download_dir) if f.lower().endswith(".pdf"))
    try:
        time.sleep(30)
        pdf_xpath = '//div[@role="button" and @title=\'Download "Document"\']'
        download_buttons = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.XPATH, pdf_xpath))
        )
        print(f"Found {len(download_buttons)} PDF download icons.")
        if not download_buttons:
            print("No PDF download icons found.")
            return False
        before_download = get_pdf_files()
        # Click the download button (assuming there's typically one invoice per booking)
        for button in download_buttons:
            driver.execute_script("arguments[0].scrollIntoView(true);", button)
            driver.execute_script("arguments[0].click();", button)
        # Wait for download to complete
        timeout = time.time() + 30
        while time.time() < timeout:
            after_download = get_pdf_files()
            new_files = after_download - before_download
            if new_files:
                for new_file in new_files:
                    original_path = os.path.join(download_dir, new_file)
                    new_name = f"invoice_{booking_id}.pdf"
                    renamed_path = os.path.join(download_dir, new_name)
                    try:
                            os.rename(original_path, renamed_path)
                            
                    except OSError:
                            new_name = f"invoice_{booking_id}_1.pdf"
                            renamed_path = os.path.join(download_dir, new_name)
                            os.rename(original_path, renamed_path)
                            print(f"Saved invoice as: {new_name}")
            before_download = after_download                
                            
        return True
        time.sleep(1)
        return False
    except Exception as e:
        print(f"Error downloading or renaming PDF: {e}")
        return False
def process_booking_ids(driver):
    failed_bookings = []
    try:
        with open("booking_id.txt", "r") as file:
            lines = file.readlines()
        booking_ids = []
        for line in lines:
            match = re.search(r'(\d+)', line)
            if match:
                booking_ids.append(match.group(1))
        if not booking_ids:
            print("No booking IDs found.")
            return
        for booking_id in booking_ids:
            print(f"\nProcessing Booking ID: {booking_id}")
            clear_chat(driver)  # Clear chat before sending new sequence
            steps = [
                "Hi",
                "Go to Main Menu",
                "Booking Voucher/Invoice",
                "Invoice",
                "Enter Booking Id",
                booking_id
            ]
            for step in steps:
                response = send_message_and_wait(driver, step, timeout=5)
                if not response:
                    print("No response received. Continuing anyway.")
            # Wait for invoice to show and attempt PDF download
            wait_for_followup_message(driver, timeout=5)
            success = click_pdf_download_icon(driver, booking_id)
            if not success:
                failed_bookings.append(booking_id)
    except Exception as e:
        print(f"Error in processing booking IDs: {e}")
    if failed_bookings:
        print("\nFailed to download invoices for the following booking IDs:")
        for fb in failed_bookings:
            print(fb)
        with open("failed_bookings.txt", "w") as f:
            f.write("\n".join(failed_bookings))
def main():
    driver = setup_driver()
    try:
        login_whatsapp(driver)
        if open_chat(driver, TREEBO_NAME) or open_chat(driver, TREEBO_NUMBER):
            process_booking_ids(driver)
        else:
            print("Chat opening failed")
    finally:
        print("Closing browser")
        driver.quit()
if __name__ == "__main__":
    main()
