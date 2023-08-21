# SDEV 435 HARMAN Spark API Python Module (Unofficial) POC

A proof of concept that implements a custom Python wrapper created to access the HARMAN SPARK private API used by the web app.

## Module Installation (Future Release)

The POC has no installation but the module at it's core (to be uploaded after the class) will use the following instructions:
Use the package manager [pip](https://pip.pypa.io/en/stable/) to install foobar.

```bash
pip install {future_module_name}
```

## Module Usage

```python
from {future_module_name} import Auth, API

username: str = "HARMAN Spark User"
password: str = "HARMAN Spark Password"

# Initialize Auth class and retrieve access token
auth = Auth()
token_and_expiry: dict = auth.generate_access_token(username="HARMAN Spark User", password="HARMAN Spark Pass")
access_token: str = token_and_expiry["access_token"]

# Initialize API class with access token.  Query location of all vehicles on account
api = API(access_token)
vehicle_ids = api.all_associated_vehicles()
for vehicle_id in vehicle_ids:
    print(api.query_vehicle_location(vehicle_id))
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.


## License

[MIT](https://choosealicense.com/licenses/mit/)