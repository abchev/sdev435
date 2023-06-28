from typing import Optional, Union
import requests

class API:
    """
    Class for interacting with (unofficial) Harman Spark API
    """
    #Definitions
    spark_authorization: str
    headers = {
        'authority': 'hapi-plus.spark.harman.com',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'en-US',
        'authorization': '',
        'cache-control': 'no-cache, no-store, must-revalidate',
        'expires': '0',
        'if-modified-since': 'Fra, 01 Jun 2010 00:00:00 GMT',
        'origin': 'https://ivehicle-plus.spark.harman.com',
        'pragma': 'no-cache',
        'referer': 'https://ivehicle-plus.spark.harman.com/',
        'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
    }
    
    #Constructor
    def __init__(self, spark_authorization: str):
        """
        Call API constructor with authorization header
        :param spark_authorization: Authorization header value, "{token_type} {access_token}"
        """
        self.set_spark_authorization(spark_authorization)

    #Setters
    def set_spark_authorization(self, spark_authorization: str):
        """
        Set authorization header value in spark_authorization and headers dict
        :param spark_authorization: Authorization header value to set
        """
        self.spark_authorization = spark_authorization
        self.headers['authorization'] = spark_authorization
    
    #Getters
    def get_spark_authorization(self) -> str: # This is set with the constructor so it should never be None
        """
        Get authorization header value
        """
        return self.spark_authorization

    #API Endpoints
    def query_user_self(self) -> dict:
        """
        Get information about the user
        :return: JSON response
        """
        url = "https://idam-plus.spark.harman.com/v1/users/self"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def query_user_vehicle_associations(self) -> dict:
        """
        Get information about the user's associations
        :return: JSON response
        """
        url = "https://hapi-plus.spark.harman.com/v2/user/associations/"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def query_vehicle_summary(self, vehicleId: str) -> dict:
        """
        Get information about the vehicle
        :param vehicleId: Vehicle ID
        :return: Raw JSON response from endpoint, as dict
        """
        url = f"https://hapi-plus.spark.harman.com/v2/devices/{vehicleId}/current/summary"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def query_vehicle_details(self, vehicleId: str) -> dict:
        """
        Get information about the vehicle
        Note: This is an older endpoint that refers to the "vehicleId" as the "clientId". The "vehicleId" in this endpoint is not used elsewhere
        :param vehicleId: Vehicle ID (referred to as "clientId" in this endpoint)
        :return: Raw JSON response from endpoint, as dict
        """
        url = f"https://hapi-plus.spark.harman.com/v1.0/vehicles?clientId={vehicleId}"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def query_vehicle_health(self, vehicleId: str) -> dict:
        """
        Get health information about the vehicle
        :param vehicleId: Vehicle ID
        :return: Raw JSON response from endpoint, as dict
        """
        url = f"https://hapi-plus.spark.harman.com/v2/devices/{vehicleId}/current/health"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def query_vehicle_location(self, vehicleId: str) -> dict:
        """
        Get location information about the vehicle
        :param vehicleId: Vehicle ID
        :return: Raw JSON response from endpoint, as dict
        """
        url = f"https://hapi-plus.spark.harman.com/v2/devices/{vehicleId}/current/location"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def query_vehicle_geofence(self, vehicleId: str) -> dict:
        """
        Get information about the vehicle's geofences (if any)
        :return: Raw JSON response from endpoint, as dict
        """
        url = f"https://hapi-plus.spark.harman.com/v1.1/devices/{vehicleId}/geofence"
        response = requests.get(url, headers=self.headers)
        return response.json()

    def query_vehicle_trips(self, vehicleId: str, since: str, until: str, timezone: Optional[str] = "America/Los_Angeles"):
        """
        Get information about the vehicle's trips
        Notes:
            Speed is in km/h regardless of settings
            Whole week is returned in summary
            Provides lat, long, speed, direction every second
            How direction translates into degrees is unknown
        :param vehicleId: Vehicle ID
        :param since: Start date of the trip (yyyy-mm-dd), must be Sunday
        :param until: End date of the trip (yyy-mm-dd), must be following Saturday
        :param timezone: Timezone of the trip
        :return: JSON response
        """
        url = f"https://hapi-plus.spark.harman.com/v2/devices/{vehicleId}/trips?since={since}&until={until}&timezone={timezone}"
        response = requests.get(url, headers=self.headers)
        return response.json()

    #Parsing Methods
    def first_associated_vehicle(self) -> Union[str, None]:
        """
        Get the first associated (active) vehicle ID to be found
        :return: Vehicle ID
        """
        vehicles = self.query_user_vehicle_associations()
        for vehicle in vehicles:
            if vehicle['associationStatus'] == 'ASSOCIATED':
                return vehicle['vehicleId']
        return None
    
    def all_associated_vehicles(self) -> list:
        """
        Get a list of all associated vehicles
        :return: List of associated vehicles
        """
        vehicles = self.query_user_vehicle_associations()
        associated_vehicles = []
        for vehicle in vehicles:
            if vehicle['associationStatus'] == 'ASSOCIATED':
                associated_vehicles.append(vehicle['vehicleId'])
        return associated_vehicles