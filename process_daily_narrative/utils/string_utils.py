import datetime
import re, json
import os

from utils.db_init import PROJECT_TIMEZONE


def clean_and_parse_json(raw_string):
    # Remove any leading/trailing whitespace
    raw_string = raw_string.strip()
    
    # Remove code block markers if present
    raw_string = re.sub(r'^```json\s*|\s*```$', '', raw_string, flags=re.MULTILINE)
    
    try:
        # Parse the JSON
        parsed_json = json.loads(raw_string)
        return parsed_json
    except json.JSONDecodeError as e:
        return f"Error parsing JSON: {str(e)}"




def get_user_input_document_path(user_input_id):
    gh_date_str = datetime.datetime.now(PROJECT_TIMEZONE).strftime('%Y-%m-%d')
    return f"daily_data/{gh_date_str}/inputs/user_inputs/{user_input_id}"

