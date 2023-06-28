from POC.db import DB
from SDEV435.SDEV435 import Auth
import pandas as pd
import datetime


class POC:
    """
    Class that stores methods directly related to the proof of concept
    """

    db: DB = DB()
    auth: Auth = Auth()

    def __init__(self):
        """
        Initializes the POC class
        """
        pass

    def auth_with_api(self, username: str, password: str) -> dict:
        """
        Generates a new token from the Spark API and stores it in the database
        :param username: Username to be used for authentication against the Spark API
        :param password: Password to be used for authentication against the Spark API
        """
        access_details = self.auth.generate_access_token(username, password)
        print("Called auth_with_api() and passed")
        dt = datetime.datetime.fromtimestamp(access_details["expires_at"], datetime.timezone.utc)
        expires_at = dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        self.db.insert_update_auth_data(self.constant_hash(username), self.constant_hash(password), access_details["access_token"], expires_at)
        return {"access_token": access_details["access_token"], "expires_at": expires_at}

    def attempt_auth_flow(self, username: str, password: str) -> dict:
        """
        Attempts to check the database for an existing token, and if it exists, checks if it is expired.
        If the token is expired or the credentials otherwise do not match it will generate a new token against the Spark API.
        :param username: Username to be used for authentication against the Spark API
        :param password: Password to be used for authentication against the Spark API
        """
        # 
        # if self.db.username_exists(self.constant_hash(username)):
        if self.db.password_matches(self.constant_hash(username), self.constant_hash(password)):
            user_token_details: dict = self.db.get_user_token_details(self.constant_hash(username))
            user_token = user_token_details["user_token"]
            user_token_expire_dt_tm = user_token_details["user_token_expire_dt_tm"]
            token_is_valid = user_token_expire_dt_tm > pd.Timestamp.utcnow() - pd.Timedelta(minutes = 1)
            if token_is_valid:
                # User/pass is valid and token is not expired (or within 1 minute of expiring)
                return {"access_token": user_token, "expires_at": user_token_expire_dt_tm}
        return self.auth_with_api(username, password)

    def constant_hash(self, s: str) -> int:
        """
        Hashes a string using a constant hash function, which is not cryptographically secure.
        Good enough for a POC that could honestly store plaintext and be fine.
        :param s: String to be hashed
        :return: Hashed string"""
        h = 0
        for c in s:
            h = (h*1217 ^ ord(c)*1847) & 0xFFFFFFFF
        return h
    