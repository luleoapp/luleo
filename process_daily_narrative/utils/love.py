import os 
from utils.llm_utils import call_and_log_llm
from utils.db_init import db
from openai import OpenAI
from utils.logger_config import system_logger
from firebase_admin import firestore
import re


def compute_love_summary(limit=10):
    # Path to the prompts directory
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    
    # Read the Luleo system prompt
    with open(os.path.join(prompts_dir, 'luleo.prompt'), 'r') as f:
        luleo_prompt = f.read()
    
    # Read the summarize wisdom prompt
    with open(os.path.join(prompts_dir, 'summarize_love.prompt'), 'r') as f:
        summarize_love_prompt = f.read()

    # Query the most recent wisdom entries
    love_query = db.collection('love_understanding').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
    love_docs = love_query.get()

    # Collate the wisdom entries into a paragraph
    love_paragraph = "\n".join([doc.to_dict()['content'] for doc in love_docs])

    # Prepare the prompt for ChatGPT
    filled_prompt = summarize_love_prompt.replace('{{LOVE_PERSPECTIVES}}', love_paragraph)
    client = OpenAI()


    try:

        response_json = call_and_log_llm(system_prompt=luleo_prompt, user_prompt=filled_prompt, model="gpt-4o")
        love_summary = response_json.get("love_summary")
        assert love_summary, "Love summary not found in the response"
        return { "summary": love_summary }

    except Exception as e:
        print(f"Error generating love summary: {e}")
        return None

