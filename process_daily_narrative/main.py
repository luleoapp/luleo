#!/usr/bin/env python3
from flask import Flask, request, jsonify
import os
from flask_cors import CORS
from src.function_map import function_map
from utils.logger_config import system_logger
import traceback
import sys
from utils.logger_config import upload_logs_to_github

app = Flask(__name__)
# By default, a route only answers to GET requests.
CORS(app)

def parse_request(type, params):
    system_logger.info(f"GOT REQUEST TYPE - {type} PARAMS {params}")
    func_to_apply = function_map.func_map.get(type, system_logger.info)
    return func_to_apply(**params)

@app.route('/', methods=['GET', 'POST'])
def call_default_cloud_run():
    system_logger.info("Received request")
    system_logger.info(f"Request method: {request.method}")
    system_logger.info(f"Request headers: {request.headers}")
    system_logger.info(f"Request data: {request.data}")
    
    try:
        req_json_dict = request.get_json(force=True)
        system_logger.info(f"Request JSON: {req_json_dict}")
    except Exception as e:
        system_logger.error(f"Error parsing JSON: {str(e)}")
        return jsonify({"error": "Invalid JSON in request body"}), 400

    request_type = req_json_dict.get('REQUEST_TYPE', None)
    request_params = req_json_dict.get('PARAMS', {})
    
    system_logger.info(f"REQUEST_TYPE: {request_type}")
    system_logger.info(f"PARAMS: {request_params}")

    if not request_type:
        system_logger.error("REQUEST_TYPE is missing")
        return jsonify({"error": "REQUEST_TYPE is required"}), 400

    try:
        func_to_apply = function_map.func_map.get(request_type)
        if func_to_apply is None:
            system_logger.warning(f"Unknown REQUEST_TYPE: {request_type}")
            return jsonify({"error": f"Unknown REQUEST_TYPE: {request_type}"}), 400

        system_logger.info(f"Applying function: {func_to_apply.__name__}")
        ret_val = func_to_apply(**request_params)
        system_logger.info(f"Function returned: {ret_val}")

        if ret_val is not None:
            return jsonify(ret_val)
        else:
            system_logger.warning(f"Function returned None for REQUEST_TYPE: {request_type}")
            return jsonify({"warning": f"No return value for REQUEST_TYPE: {request_type}"}), 204
 
    except Exception as e:
        system_logger.error(f"Error in {request_type} {request_params}")
        system_logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        upload_logs_to_github()


if __name__ == "__main__":
    system_logger.info("DEBUGGING THIS APP")
    system_logger.info(f"Python executable: {sys.executable}")
    system_logger.info(f"Python version: {sys.version}")
    system_logger.info(f"Virtual environment: {os.environ.get('VIRTUAL_ENV')}")
    myhost = os.uname()[1]
    system_logger.info(f"Testing this - {myhost}")
    app.run(debug=False, host='0.0.0.0', port=int(
        os.environ.get('PORT', 8080)))
