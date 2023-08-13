from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import re
import time
from typing import Optional

class Auth:
    """
    Class to handle authentication with Harman Spark online portal
    """
    #Definitions
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    expires_at: Optional[int] = None

    def generate_access_token(self, username: str, password: str, sleep_after_auth_seconds: float = 2) -> dict:
        """
        Uses Selenium to get access token from Harman Spark API
        :param username: Username to be used for authentication against the Spark API
        :param password: Password to be used for authentication against the Spark API
        :param sleep_after_auth_seconds: Number of seconds to sleep after authentication to allow JS to load
        :return: Dict of access_token, expires_at
        """
        # Set up Chrome options to run headless with minimal logging
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-crash-reporter")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-in-process-stack-traces")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--log-level=3")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://ivehicle-plus.spark.harman.com/")
        
        # Sleep to allow JS to load and redirect
        time.sleep(sleep_after_auth_seconds)
        username_field = driver.find_element(By.CSS_SELECTOR, 'input#username')
        password_field = driver.find_element(By.CSS_SELECTOR, 'input#password')
        login_button_div = driver.find_element(By.CSS_SELECTOR, 'div.sign-in-custom')
        login_button = login_button_div.find_element(By.CSS_SELECTOR, 'button')

        #Plaintext username and password over HTTPS
        username_field.send_keys(username)
        password_field.send_keys(password)
        time.sleep(sleep_after_auth_seconds)
        login_button.click()
        authed_url = driver.current_url
        try:
            access_token, token_type, expires_in = re.findall(r'access_token=(.*?)&token_type=(.*?)&expires_in=([0-9]*)', authed_url)[0]
        except IndexError:
            raise Exception("Unable to authenticate with Harman Spark API")
        
        self.access_token = access_token
        self.token_type = token_type
        self.expires_at = int(time.time()) + int(expires_in)
        return {"access_token": f"{token_type} {access_token}", "expires_at": self.expires_at}

    #Getters
    def get_access_token(self) -> Optional[str]:
        """
        Retrieve already generated access token
        :return: Access token, or None if not generated
        """
        return self.access_token
    
    def get_token_type(self) -> Optional[str]:
        """
        Retrieve already generated token type (currently always "Bearer")
        :return: Token type, or None if not generated
        """
        return self.token_type
    
    def get_expires_at(self) -> Optional[int]:
        """
        Retrieve already generated expiration time in epoch seconds
        :return: Expiration time, or None if not generated
        """
        return self.expires_at