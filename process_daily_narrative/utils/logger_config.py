import logging
import os
from datetime import datetime
from utils.drive import upload_file_to_github
from utils.db_init import PROJECT_TIMEZONE

def setup_logger():
    logger = logging.getLogger('process_daily_narrative')
    logger.setLevel(logging.INFO)

    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    # Create file handler and set level to INFO
    current_date = datetime.now(PROJECT_TIMEZONE).strftime('%Y-%m-%d')
    log_file = os.path.join(logs_dir, f'log_{current_date}.txt')
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
logger, log_file_path = setup_logger()

def upload_log_to_github():
    try:
        github_path = f'logs/log_{datetime.now(PROJECT_TIMEZONE).strftime("%Y-%m-%d.%H.%M.%S")}.txt'
        upload_file_to_github(log_file_path, github_path)
        logger.info(f"Log file uploaded to GitHub: {github_path}")
    except Exception as e:
        logger.error(f"Failed to upload log file to GitHub: {e}")