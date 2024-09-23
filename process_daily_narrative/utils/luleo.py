import os 
from utils.db_init import db
from utils.logger_config import logger
from firebase_admin import firestore

def get_luleo_prompt():

    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    
    # Read the Luleo system prompt
    with open(os.path.join(prompts_dir, 'luleo.prompt'), 'r') as f:
        base_prompt = f.read()  
    
    #add summary
    summary = get_latest_summary()

    prompt = base_prompt.replace("{{WISDOM_SUMMARY}}", summary['wisdom_summary']).replace("{{LOVE_SUMMARY}}", summary['love_summary'])

    return prompt


def get_latest_summary():
    # Get the latest summary from the summary collection
    docs = db.collection("summary").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).get()
    if len(docs) == 0:
        logger.error(f"No summary found")
        return None
    return docs[0].to_dict()

