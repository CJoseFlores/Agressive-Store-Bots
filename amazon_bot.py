import bs4
import sys
import time
import logging
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from twilio.base.exceptions import TwilioRestException

from amazon_credentials import AmazonCredentials
from twilio_client_wrapper import TwilioClientWrapper


class AmazonBot:
    def __init__(self,
                 twilio_wrapper: TwilioClientWrapper,
                 firefox_profile_path: str,
                 amazon_credentials: AmazonCredentials,
                 amazon_store_url: str):
        self.amazon_credentials = amazon_credentials
        self.store_url = amazon_store_url
        self.twilio_wrapper = twilio_wrapper
        self.firefox_profile_path = firefox_profile_path

        # FIXME: This is AWFUL. Move the driver creation outside of this class.
        try:
            self.driver = self.create_driver()
        except FileNotFoundError:
            print("Could not find the file '" + firefox_profile_path + "'")
            sys.exit(1)

    def create_driver(self):
        """Creating driver."""
        options = Options()
        options.headless = False  # Change To False if you want to see Firefox Browser Again.
        profile = webdriver.FirefoxProfile(self.firefox_profile_path)
        driver = webdriver.Firefox(profile, options=options, executable_path=GeckoDriverManager().install())
        return driver

    def time_sleep(self, x):
        for i in range(x, -1, -1):
            sys.stdout.write('\r')
            sys.stdout.write('{:2d} seconds'.format(i))
            sys.stdout.flush()
            time.sleep(1)
        self.driver.execute_script('window.localStorage.clear();')
        self.driver.refresh()
        sys.stdout.write('\r')
        sys.stdout.write('Page refreshed\n')
        sys.stdout.flush()

    def driver_wait(self, find_type, selector):
        """Driver Wait Settings."""
        while True:
            if find_type == 'css':
                try:
                    self.driver.find_element_by_css_selector(selector).click()
                    break
                except NoSuchElementException:
                    self.driver.implicitly_wait(0.2)
            elif find_type == 'name':
                try:
                    self.driver.find_element_by_name(selector).click()
                    break
                except NoSuchElementException:
                    self.driver.implicitly_wait(0.2)

    def login_attempt(self):
        """Attempting to login Amazon Account."""
        self.driver.get('https://www.amazon.com/gp/sign-in.html')
        try:
            username_field = self.driver.find_element_by_css_selector('#ap_email')
            username_field.send_keys(self.amazon_credentials.username)
            self.driver_wait('css', '#continue')
            password_field = self.driver.find_element_by_css_selector('#ap_password')
            password_field.send_keys(self.amazon_credentials.password)
            self.driver_wait('css', '#signInSubmit')
            time.sleep(2)
        except NoSuchElementException:
            pass
        self.driver.get(self.store_url)

    def finding_cards(self):
        """Scanning all cards."""
        while True:
            time.sleep(1)
            html = self.driver.page_source
            soup = bs4.BeautifulSoup(html, 'html.parser')
            try:
                find_all_cards = soup.find_all('span', {'class': 'style__text__2xIA2'})
                for card in find_all_cards:
                    if 'Add to Cart' in card.get_text():
                        print('Card Available!')
                        self.driver_wait('css', '.style__addToCart__9TqqV')
                        self.driver.get('https://www.amazon.com/gp/cart/view.html?ref_=nav_cart')
                        self.driver_wait('css', '.a-button-input')
                        try:
                            asking_to_login = self.driver.find_element_by_css_selector('#ap_password').is_displayed()
                            if asking_to_login:
                                self.driver.find_element_by_css_selector('#ap_password') \
                                    .send_keys(self.amazon_credentials.password)
                                self.driver_wait('css', '#signInSubmit')
                        except NoSuchElementException:
                            pass
                        self.driver_wait('css', '.a-button-input')  # Final Checkout Button!
                        logging.info('Order Placed')
                        try:
                            self.twilio_wrapper.client.messages.create(to=self.twilio_wrapper.to_number,
                                                                       from_=self.twilio_wrapper.from_number,
                                                                       body='ORDER PLACED!')
                        except (NameError, TwilioRestException):
                            pass
                        for i in range(3):
                            print('\a')
                            time.sleep(1)
                        time.sleep(1800)
                        self.driver.quit()
                        return
            except (AttributeError, NoSuchElementException, TimeoutError):
                pass
            self.time_sleep(5)
