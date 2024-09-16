#!/usr/bin/env python3
from flask import Flask, request, jsonify
import os
from flask_cors import CORS
from src.function_map import function_map
from utils.logger_config import logger
import traceback
import sys


app = Flask(__name__)
# By default, a route only answers to GET requests.
CORS(app)


def parse_request(type, params):
    logger.info(f"GOT REQUEST TYPE - {type} PARAMS {params}")
    func_to_apply = function_map.func_map.get(type, logger.info)
    return func_to_apply(**params)

    #return {"test" : True}


@app.route('/', methods=['GET', 'POST'])
def call_default_cloud_run():
    logger.info("Received request")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request headers: {request.headers}")
    logger.info(f"Request data: {request.data}")
    
    try:
        req_json_dict = request.get_json(force=True)
        logger.info(f"Request JSON: {req_json_dict}")
    except Exception as e:
        logger.error(f"Error parsing JSON: {str(e)}")
        return jsonify({"error": "Invalid JSON in request body"}), 400

    request_type = req_json_dict.get('REQUEST_TYPE', None)
    request_params = req_json_dict.get('PARAMS', {})
    
    logger.info(f"REQUEST_TYPE: {request_type}")
    logger.info(f"PARAMS: {request_params}")

    if not request_type:
        logger.error("REQUEST_TYPE is missing")
        return jsonify({"error": "REQUEST_TYPE is required"}), 400

    try:
        func_to_apply = function_map.func_map.get(request_type)
        if func_to_apply is None:
            logger.warning(f"Unknown REQUEST_TYPE: {request_type}")
            return jsonify({"error": f"Unknown REQUEST_TYPE: {request_type}"}), 400

        logger.info(f"Applying function: {func_to_apply.__name__}")
        ret_val = func_to_apply(**request_params)
        logger.info(f"Function returned: {ret_val}")

        if ret_val is not None:
            return jsonify(ret_val)
        else:
            logger.warning(f"Function returned None for REQUEST_TYPE: {request_type}")
            return jsonify({"warning": f"No return value for REQUEST_TYPE: {request_type}"}), 204

    except Exception as e:
        logger.error(f"Error in {request_type} {request_params}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

    logger.warning(f"Reached end of function without return for REQUEST_TYPE: {request_type}")
    return jsonify({"warning": f"REQUEST_TYPE was {request_type}"}), 204


if __name__ == "__main__":
    # app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
    # print("Hello")
    '''
    parser = argparse.ArgumentParser(description='Traverse and download files from a Google Drive folder.')
    parser.add_argument('-c','--create_folder', action='store_true', help='Create folder')
    args = parser.parse_args()
    if args.create_folder:
        create_daily_folder()
    '''
    logger.info("DEBUGGING THIS APP")
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Virtual environment: {os.environ.get('VIRTUAL_ENV')}")
    myhost = os.uname()[1]
    logger.info(f"Testing this - {myhost}")
    app.run(debug=False, host='0.0.0.0', port=int(
        os.environ.get('PORT', 8080)))
    # Parse command line arguments
    
    #args = parser.parse_args()
   

    # usage
    #bucket_name = 'your-bucket-name'
    #source_file_name = 'daily_vibes.xml'
    #destination_folder_name = 'daily_narrative'

    
    '''
    # Convert date to folder name format (e.g., "20240516" -> "May 16, 2024")
    folder_name = datetime.strptime(args.date, '%Y%m%d').strftime('%B %-d, %Y')
    date_folder = find_subfolder_id(os.environ["GOOGLE_DRIVE_LULEO_FOLDER_ID"], folder_name)
    d_date_folder = create_initialize_subfolders(os.environ["GOOGLE_DRIVE_LULEO_FOLDER_ID"],[folder_name])
    d_folders = create_initialize_subfolders(d_date_folder[folder_name.lower()],["Inputs","Vibes"])
    inputs_subfolders = create_initialize_subfolders(d_folders["inputs"], ["AI Developments", "Combined","Luleo Updates","News"])
    vibes_subfolders = create_initialize_subfolders(d_folders["vibes"],["Luleo Generated Vibes", "User Contributions"])
    
    news = write_daily_news_file(subfolder_id=inputs_subfolders["news"])
    write_articles = write_substack_pdfs()
    '''    
