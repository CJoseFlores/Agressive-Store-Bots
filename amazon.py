import bs4
import sys
import time
import logging
import argparse
import configparser
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from twilio.rest import Client
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from twilio.base.exceptions import TwilioRestException

# TODO: Move all of this somewhere else. Having the default values of empty string sucks.

# Amazon config
username = ""
password = ""
store_url = "https://www.amazon.com/stores/GeForce/RTX3080_GEFORCERTX30SERIES/page/6B204EA4-AAAC-4776-82B1-D7C3BD9DDC82"

# Twilio configuration
to_number = ""
from_number = ""
account_sid = 'blah'
auth_token = 'blah'
client = Client(account_sid, auth_token)

# Firefox config
firefox_profile_path = r'C:\Users\Trebor\AppData\Roaming\Mozilla\Firefox\Profiles\kwftlp36.default-release'

# Constant Strings
amazon_config_key = 'amazon-config'
twilio_config_key = 'twilio-config'
firefox_config_key = 'firefox-config'

def time_sleep(x, driver):
    for i in range(x, -1, -1):
        sys.stdout.write('\r')
        sys.stdout.write('{:2d} seconds'.format(i))
        sys.stdout.flush()
        time.sleep(1)
    driver.execute_script('window.localStorage.clear();')    
    driver.refresh()
    sys.stdout.write('\r')
    sys.stdout.write('Page refreshed\n')
    sys.stdout.flush()


def create_driver():
    """Creating driver."""
    options = Options()
    options.headless = False  # Change To False if you want to see Firefox Browser Again.
    profile = webdriver.FirefoxProfile(firefox_profile_path)
    driver = webdriver.Firefox(profile, options=options, executable_path=GeckoDriverManager().install())
    return driver


def driver_wait(driver, find_type, selector):
    """Driver Wait Settings."""
    while True:
        if find_type == 'css':
            try:
                driver.find_element_by_css_selector(selector).click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(0.2)
        elif find_type == 'name':
            try:
                driver.find_element_by_name(selector).click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(0.2)


def login_attempt(driver):
    """Attempting to login Amazon Account."""
    driver.get('https://www.amazon.com/gp/sign-in.html')
    try:
        username_field = driver.find_element_by_css_selector('#ap_email')
        username_field.send_keys(username)
        driver_wait(driver, 'css', '#continue')
        password_field = driver.find_element_by_css_selector('#ap_password')
        password_field.send_keys(password)
        driver_wait(driver, 'css', '#signInSubmit')
        time.sleep(2)
    except NoSuchElementException:
        pass
    driver.get(store_url)


def finding_cards(driver):
    """Scanning all cards."""
    while True:
        time.sleep(1)
        html = driver.page_source
        soup = bs4.BeautifulSoup(html, 'html.parser')
        try:
            find_all_cards = soup.find_all('span', {'class': 'style__text__2xIA2'})
            for card in find_all_cards:
                if 'Add to Cart' in card.get_text():
                    logging.info('Card Available!')
                    driver_wait(driver, 'css', '.style__addToCart__9TqqV')
                    driver.get('https://www.amazon.com/gp/cart/view.html?ref_=nav_cart')
                    driver_wait(driver, 'css', '.a-button-input')
                    try:
                        asking_to_login = driver.find_element_by_css_selector('#ap_password').is_displayed()
                        if asking_to_login:
                            driver.find_element_by_css_selector('#ap_password').send_keys(password)
                            driver_wait(driver, 'css', '#signInSubmit')
                    except NoSuchElementException:
                        pass
                    driver_wait(driver, 'css', '.a-button-input')  # Final Checkout Button!
                    logging.info('Order Placed')
                    try:
                        client.messages.create(to=to_number, from_=from_number, body='ORDER PLACED!')
                    except (NameError, TwilioRestException):
                        pass
                    for i in range(3):
                        print('\a')
                        time.sleep(1)
                    time.sleep(1800)
                    driver.quit()
                    return
        except (AttributeError, NoSuchElementException, TimeoutError):
            pass
        time_sleep(5, driver)


if __name__ == '__main__':
    # Load arguments
    parser = argparse.ArgumentParser(description='Bot that buys items from amazon storefronts.')
    parser.add_argument('-f', '--file', dest='file_path', default='bot-config.ini', help='The path to the bot '
                                                                                         'configuration file ('
                                                                                         'defaults to relative file: '
                                                                                         'bot-config.ini)')
    config_file_path = parser.parse_args().file_path

    # Load configuration file
    try:
        with open(config_file_path, 'r+') as f:
            config_file = f.read()

        config = configparser.ConfigParser()
        config.read(config_file_path, encoding='utf-8-sig')
    except configparser.MissingSectionHeaderError:
        print("There was an error loading the config file. Make sure your headers are enclosed in brackets '[]'. "
              "Exiting...")
        sys.exit(1)
    except FileNotFoundError:
        print("Could not find or open file referenced by path: " + config_file_path)
        sys.exit(1)

    # Parse the amazon configuration
    if amazon_config_key in config:
        try:
            username = config[amazon_config_key]['username']
            password = config[amazon_config_key]['password']
            store_url = config[amazon_config_key]['storeUrl']
        except KeyError:
            print("Missing 'username', 'password' or 'storeUrl' keywords from the [" + amazon_config_key
                  + "] config section.")
            sys.exit(1)
    else:
        print("Could not find the [" + amazon_config_key + "] config section. Exiting...")
        sys.exit(1)

    # Parse the twilio configuration
    if twilio_config_key in config:
        try:
            to_number = config[twilio_config_key]['toNumber']
            from_number = config[twilio_config_key]['fromNumber']
            account_sid = config[twilio_config_key]['accountSid']
            auth_token = config[twilio_config_key]['authToken']
            client = Client(account_sid, auth_token)
        except KeyError:
            print("Missing one or all of the config keywords from the [" + twilio_config_key + "] config section:"
                  + "'toNumber', 'fromNumber', 'accountSid', 'authToken'.")
            sys.exit(1)
    else:
        print("Could not find the [" + twilio_config_key + "] config section. Exiting...")
        sys.exit(1)

        # Parse the firefox configuration
    if firefox_config_key in config:
        try:
            # Encode the profile path with unicode-escape to escape windows back slashes in the bath.
            firefox_profile_path = config[firefox_config_key]['profilePath'].encode('unicode-escape').decode()
        except KeyError:
            print("Missing config keyword 'profilePath' from the config section [" + firefox_config_key + "].")
            sys.exit(1)
    else:
        print("Could not find the [" + firefox_config_key + "] config section. Exiting...")

    driver = create_driver()
    login_attempt(driver)
    finding_cards(driver)