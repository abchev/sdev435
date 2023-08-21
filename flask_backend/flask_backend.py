# Bring parent directory into scope to import modules dir without having to install the package
import os
import sys
import pathlib
sys.path.append(str(pathlib.Path(os.path.dirname(os.path.realpath(__file__))).parent))

import flask
import inspect
from typing import List
from modules.hsparkapi.api import API
from modules.hsparkapi.auth import Auth
from POC.db import DB
from POC.poc import POC

app = flask.Flask(__name__)

auth: Auth = Auth()

@app.route('/query/<endpoint>', methods=['POST'])
def query(endpoint):
    """
    Dynamic route that expects a JSON body with the vehicleId parameter if the endpoint requires it.
    Returns a JSON with the data from the endpoint formatted as {"data": <raw endpoint data>}
    """
    authorization: str = flask.request.headers.get("Authorization")
    api = API(authorization)
    endpoints: list = ["_".join(method.split("_")[1:]) for method in dir(API) if method.startswith("query_") and method != "query_vehicle_trips"]
    endpoint_methods: dict = {endpoint: getattr(api, f"query_{endpoint}") for endpoint in endpoints}
    if endpoint not in endpoint_methods:
        return flask.jsonify({'error': 'Invalid endpoint'})
    method = endpoint_methods[endpoint]
    uses_vehId: bool = "vehicleId" in method.__code__.co_varnames
    if uses_vehId:
        try:
            vehicle_id = flask.request.json["vehicleId"]
        except KeyError:
            return flask.jsonify({'error': 'Missing vehicleId'})
        finally:
            return flask.jsonify({"data": method(vehicle_id)})
    else:
        return flask.jsonify({"data": method()})
    
@app.route('/query/available_endpoints', methods=['GET'])
def available_endpoints():
    """
    Static route that returns a JSON with all available endpoints and their descriptions.
    """
    endpoints: List[str] = ["_".join(method.split("_")[1:]) for method in dir(API) if method.startswith("query_") and method != "query_vehicle_trips"]
    resp = []
    for endpoint in endpoints:
        resp.append({
            "name": endpoint.replace("_", " ").title(),
            "endpoint": f"query/{endpoint}", 
            "description": getattr(API, f"query_{endpoint}").__doc__.split("\n")[1].strip(),
            "parameters": list(inspect.signature(getattr(API, f"query_{endpoint}")).parameters.keys())[1:]
        })
    return flask.jsonify({"data": resp})

@app.route('/auth', methods=['POST'])
def auth():
    """
    Static route that expects a JSON body with username and password.
    Returns a JSON with the credentials if the authentication was successful.
    """
    username = flask.request.json["username"]
    password = flask.request.json["password"]
    try:
        credentials = POC().attempt_auth_flow(username, password)
    except Exception as e:
        return flask.jsonify({"error": str(e)})
    return flask.jsonify({"data": credentials})

@app.route('/db/default_vehicle_id', methods=['POST'])
def default_vehicle_id():
    """
    Static route that expects a JSON body with username.
    Returns a JSON with the default vehicle id for the user.
    """
    username = flask.request.json["username"]
    hashed_username = POC().constant_hash(username)
    return flask.jsonify({"data": {"default_vehicle_id": DB().get_default_vehicle_id(hashed_username)}})

@app.route('/ping', methods=['GET', 'POST'])
def ping():
    """
    Static route that returns a JSON with the message "pong".
    """
    return flask.jsonify({'message': 'pong'})

if __name__ == '__main__':
    app.run(host="192.168.1.166", port="5000", debug=True)