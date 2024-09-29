import logging
import os
from datetime import datetime
from utils.github_utils import upload_file_to_github
from utils.db_init import PROJECT_TIMEZONE
import uuid

def setup_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), f'logs/{name}')
    os.makedirs(logs_dir, exist_ok=True)

    # Create file handler and set level to INFO
    curr_dt = datetime.now(PROJECT_TIMEZONE).strftime("%Y-%m-%d.")
    random_str = str(uuid.uuid4())[:6]
    log_file = os.path.join(logs_dir, f'log_{curr_dt}_{random_str}.txt')
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    # Create console handler and set level to INFO
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Add formatter to handlers
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger, log_file

# Create and configure logger
system_logger, system_log_file_path = setup_logger('system')
llm_logger, llm_log_file_path = setup_logger('llm')


def upload_logs_to_github():
    for logger_name, logger, log_file_path in [('system', system_logger, system_log_file_path), ('llm', llm_logger, llm_log_file_path)]:
        try:
            github_path = f'logs/{logger_name}/log_{datetime.now(PROJECT_TIMEZONE).strftime("%Y-%m-%d.%H.%M.%S")}.txt'
            upload_file_to_github(log_file_path, github_path)
            system_logger.info(f"Log file uploaded to GitHub: {github_path}")
        except Exception as e:
            system_logger.error(f"Failed to upload log file to GitHub: {e}")

    