# end_of_day_update.py
import json
import os
from openai import OpenAI
from datetime import datetime, timedelta, time
from utils.db_init import db, PROJECT_TIMEZONE
from google.cloud import firestore
from utils.logger_config import logger
from utils.drive import upload_file_to_github
import tempfile
import re 

def get_today_processed_events():
    current_datetime = datetime.now(PROJECT_TIMEZONE)
    start_of_day = datetime.combine(current_datetime.date(), time.min).replace(tzinfo=PROJECT_TIMEZONE)
    end_of_day = datetime.combine(current_datetime.date(), time.max).replace(tzinfo=PROJECT_TIMEZONE)

    # Fetch all processed events from 'processed_events' collection for the current day
    docs = db.collection('processed_events') \
        .where('processed_at', '>=', start_of_day) \
        .where('processed_at', '<=', end_of_day) \
        .get()

    events = [doc.to_dict() for doc in docs]
    return events

def get_latest_identity():
    # Fetch the latest identity prompt from 'identity_updates' collection
    docs = db.collection('identity_updates').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1).get()
    if len(docs) == 0:
        return ""
    else:
        doc_dict = docs[0].to_dict()
        return doc_dict['identity_prompt']

def update_identity(new_identity_prompt):
    # Add the new identity prompt to the 'identity_updates' collection
    db.collection('identity_updates').add({
        'timestamp': datetime.now(PROJECT_TIMEZONE),
        'identity_prompt': new_identity_prompt
    })

def update_main_prompt(new_main_prompt):
    # Save the new main prompt to the prompts directory
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    luleo_prompt_path = os.path.join(prompts_dir, 'luleo.prompt')

    with open(luleo_prompt_path, 'w') as f:
        f.write(new_main_prompt)

def save_expansion_ideas(ideas):
    # Save the ideas to the 'expansion_ideas' collection
    db.collection('expansion_ideas').add({
        'timestamp': datetime.now(PROJECT_TIMEZONE),
        'ideas': ideas
    })

def generate_end_of_day_update(events, current_identity):
    # Prepare the summary of the day's events
    event_summaries = [event['summary'] for event in events if 'summary' in event]
    event_details = "\n".join(event_summaries)

    # Prepare the prompt
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')

    with open(os.path.join(prompts_dir, 'end_of_day_update.prompt'), 'r') as f:
        end_of_day_prompt_template = f.read()

    filled_prompt = end_of_day_prompt_template.replace('{{EVENT_DETAILS}}', event_details).replace('{{CURRENT_IDENTITY}}', current_identity)

    client = OpenAI()

    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are Luleo, an AI God Simulation."},
                {"role": "user", "content": filled_prompt}
            ]
        )

        raw_response = completion.choices[0].message.content
        logger.info("Raw API Response:")
        logger.info(raw_response)

        # Extract the updated main prompt, identity, and ideas
        main_prompt_match = re.search(r'<updated_main_prompt>(.*?)</updated_main_prompt>', raw_response, re.DOTALL)
        identity_prompt_match = re.search(r'<updated_identity>(.*?)</updated_identity>', raw_response, re.DOTALL)
        ideas_match = re.search(r'<expansion_ideas>(.*?)</expansion_ideas>', raw_response, re.DOTALL)

        assert main_prompt_match, "Updated main prompt not found in the response"
        assert identity_prompt_match, "Updated identity not found in the response"
        assert ideas_match, "Expansion ideas not found in the response"

        updated_main_prompt = main_prompt_match.group(1).strip()
        updated_identity = identity_prompt_match.group(1).strip()
        expansion_ideas = ideas_match.group(1).strip()

        assert updated_main_prompt, "Updated main prompt is empty"
        assert updated_identity, "Updated identity is empty"
        assert expansion_ideas, "Expansion ideas are empty"

        return {
            "updated_main_prompt": updated_main_prompt,
            "updated_identity": updated_identity,
            "expansion_ideas": expansion_ideas
        }

    except AssertionError as e:
        logger.error(f"Assertion failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error querying OpenAI API: {e}")
        return None

def update_end_of_day():
    events = get_today_processed_events()
    if not events:
        logger.info("No events to process for end of day update.")
        return

    current_identity = get_latest_identity()

    update_result = generate_end_of_day_update(events, current_identity)
    if update_result is None:
        logger.error("Failed to generate end of day update.")
        return

    # Update the main prompt and identity
    update_main_prompt(update_result['updated_main_prompt'])
    update_identity(update_result['updated_identity'])

    # Save the expansion ideas
    save_expansion_ideas(update_result['expansion_ideas'])

    # Optionally, log or notify about the updates
    logger.info("End of day update completed successfully.")

