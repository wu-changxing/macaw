import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from urllib.parse import urlparse, urlunparse


def login_to_admin():
    driver.get(f"{site}/admin/")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'id_username')))
    driver.find_element(By.ID, 'id_username').send_keys(USERNAME)
    driver.find_element(By.ID, 'id_password').send_keys(PASSWORD + Keys.RETURN)


def navigate_to_last_musings():
    driver.get(f"{site}/zh-hans/musings/")
    links = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.XPATH,
                                             '//a[starts-with(@href, "/zh-hans/musings/") and contains(@class, "text-center text-4xl")]'))
    )
    links[-1].click()


def translate_to_language(lang_code):
    new_path = urlparse(driver.current_url).path.replace('zh-hans', lang_code)
    new_url = urlunparse(
        (parsed_url.scheme, parsed_url.netloc, new_path, parsed_url.params, parsed_url.query, parsed_url.fragment))
    driver.get(new_url)

    wagtail_userbar = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'wagtail-userbar')))
    shadow_root = driver.execute_script('return arguments[0].shadowRoot', wagtail_userbar)
    # WebDriverWait(shadow_root, 15).until(EC.presence_of_element_located((By.ID, 'wagtail-userbar-trigger'))).click()

    page_id = driver.execute_script('''
        var shadowRoot = arguments[0].shadowRoot;
        var editButton = shadowRoot.querySelector('a[role="menuitem"][href*="/edit/"]');
        return editButton.getAttribute('href').split("/")[3];
    ''', wagtail_userbar)

    driver.get(f"{site}/admin/pages/{page_id}/edit/")
    try:
        button = driver.find_element(By.LINK_TEXT, "Translate this page")
        button.click()
        wait = WebDriverWait(driver, 10)  # waiting up to 10 seconds
        checkbox = wait.until(EC.element_to_be_clickable((By.ID, "id_select_all")))
        checkbox.click()

        # Click the submit button
        submit_button = driver.find_element(By.CSS_SELECTOR, 'input[type="submit"].button')
        submit_button.click()
    except:
        print("no need to add new pages")

    translate_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#tab-content > div > div:nth-child(3) > form > button"))
    )
    if not translate_button.get_attribute("disabled"):
        translate_button.click()
        try:
            publish_button = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, 'button[name="action"][value="publish"]'))
            )
            publish_button.click()
        except:
            print("Publish button not found")


# Setup
load_dotenv()
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
site = "https://aaron404.com"
# site= "http://localhost:8000"
driver = webdriver.Chrome()

# Login and Navigate to Last Musings
login_to_admin()
navigate_to_last_musings()

# Main Loop for Articles
while True:
    parsed_url = urlparse(driver.current_url)
    # Inner Loop for Translating
    for code in ["en", "ja", "it", "fr", "ar", "es", "pt", "ru", "ko", "de"]:
        translate_to_language(code)
        driver.get(parsed_url.geturl())

    # Go to Next Article
    next_page_link = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div.text-sky-600 > a'))
    )
    if next_page_link.text.strip() == '<':
        break
    next_page_link.click()

