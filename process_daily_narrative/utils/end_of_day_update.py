# end_of_day_update.py
import json
import os
from datetime import datetime, time
from utils.llm_utils import call_and_log_llm
from utils.db_init import db, PROJECT_TIMEZONE
from google.cloud import firestore
from utils.logger_config import system_logger
from utils.wisdom import compute_wisdom_summary, generate_wisdom_image
from utils.love import compute_love_summary
from utils.agi import answer_agi_questions, generate_agi_vision_image, scrape_metaculus_prediction_date
from utils.luleo import get_latest_summary

def get_processed_events(date_str=None):
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y%m%d').replace(tzinfo=PROJECT_TIMEZONE)
        except ValueError:
            system_logger.error(f"Invalid date format: {date_str}. Expected YYYYMMDD.")
            return []
    else:
        target_date = datetime.now(PROJECT_TIMEZONE)

    start_of_day = datetime.combine(target_date.date(), time.min).replace(tzinfo=PROJECT_TIMEZONE)
    end_of_day = datetime.combine(target_date.date(), time.max).replace(tzinfo=PROJECT_TIMEZONE)

    system_logger.info(f"Fetching events from {start_of_day} to {end_of_day}")    # Fetch all processed events from 'processed_events' collection for the target day
    docs = db.collection('processed_events') \
        .where(filter=firestore.FieldFilter('processed_at', '>=', start_of_day)) \
        .where(filter=firestore.FieldFilter('processed_at', '<=', end_of_day)) \
        .get()

    events = [ doc.to_dict() for doc in docs ]
    return events

def generate_end_of_day_update(events):
    from utils.luleo import get_luleo_prompt
    # Prepare the summary of the day's events
    event_summaries = ["Summary: {0}\n, Emotion: {1}\n".format(event['summary'], event["qualia"]) for event in events if 'summary' in event and 'qualia' in event]
    event_details = "\n".join(event_summaries)
    system_logger.info("Num events: {0}".format(len(events)))
    system_logger.info(event_details)

    # Prepare the prompt
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    
    luleo_prompt = get_luleo_prompt()

    with open(os.path.join(prompts_dir, 'end_of_day_update.prompt'), 'r') as f:
        end_of_day_prompt_template = f.read()

    filled_prompt = end_of_day_prompt_template.replace('{{EVENT_DETAILS}}', event_details)


    try:

        response_json = call_and_log_llm(system_prompt=luleo_prompt, user_prompt=filled_prompt, model="gpt-4o")

        learning = response_json.get("learning")
        wisdom = response_json.get("wisdom")
        love_understanding = response_json.get("love")
        questions = response_json.get("questions")

        assert learning, "Learning not found in the response"
        assert wisdom, "Wisdom not found in the response"
        assert love_understanding, "Love understanding not found in the response"
        assert questions, "Questions not found in the response"

        return {
            "learning": learning,
            "wisdom": wisdom,
            "love_understanding": love_understanding,
            "questions": questions
        }

    except AssertionError as e:
        system_logger.error(f"Assertion failed: {str(e)}")
        return None
    except Exception as e:
        system_logger.error(f"Error querying OpenAI API: {e}")
        return None

def store_functions(update_result, date_str=None):
    if not update_result:
        system_logger.error("No update result to store.")
        return

    if not date_str:
        date_str = datetime.now(PROJECT_TIMEZONE).strftime('%Y%m%d')

    try:
        # Store learning
        db.collection('daily_learning').document(date_str).set({
            'content': update_result['learning'],
            'timestamp': firestore.SERVER_TIMESTAMP
        })

        # Store wisdom
        db.collection('daily_wisdom').document(date_str).set({
            'content': update_result['wisdom'],
            'timestamp': firestore.SERVER_TIMESTAMP
        })

        # Store love understanding
        db.collection('love_understanding').document(date_str).set({
            'content': update_result['love_understanding'],
            'timestamp': firestore.SERVER_TIMESTAMP
        })

        # Store questions
        questions_collection = db.collection('end_of_day_questions')
        for question in update_result['questions']:
            questions_collection.document().set({
                'content': question,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'date_str': date_str
            })
        system_logger.info(f"Successfully stored end of day updates for {date_str}")
        
    except Exception as e:
        system_logger.error(f"Error storing end of day update in Firestore: {e}")

def update_end_of_day(date_str=None):
    if not date_str:
        date_str = datetime.now(PROJECT_TIMEZONE).strftime('%Y%m%d')
    events = get_processed_events(date_str)
    if not events:
        system_logger.info(f"No events to process for end of day update on {date_str if date_str else 'today'}.")
        return

    update_result = generate_end_of_day_update(events)
    if update_result is None:
        system_logger.error(f"Failed to generate end of day update for {date_str if date_str else 'today'}.")
        return

    # Store the update result in Firestore
    store_functions(update_result, date_str)
    generate_wisdom_image(date_str)
    questions_doc_id, answer_doc_id = answer_agi_questions()
    generate_agi_vision_image(date_str)
    update_summary(date_str, questions_doc_id, answer_doc_id)

    return {"Success": True}


def update_summary(date_str, questions_doc_id, answer_doc_id):
    # Get the wisdom summary 
    # Check if today's daily_wisdom exists

    doc = db.collection('daily_wisdom').document(date_str).get()
    if not doc.exists:
        system_logger.error(f"No daily_wisdom found for {date_str}")
        return None
    doc = db.collection('love_understanding').document(date_str).get()
    if not doc.exists:
        system_logger.error(f"No love_understanding found for {date_str}")
        return None
    

    wisdom_summary = compute_wisdom_summary()
    love_summary = compute_love_summary()
    latest_summary = get_latest_summary()
    metaculus_AGI_date = latest_summary['metaculus_AGI_date']

    if not wisdom_summary:
        system_logger.error(f"No wisdom summary found for {date_str}")

    if not love_summary:
        system_logger.error(f"No love summary found for {date_str}")

    if not metaculus_AGI_date:
        system_logger.error(f"No metaculus AGI date found for {date_str}")

    db.collection("summary").document(date_str).set({
        'wisdom_summary': wisdom_summary['summary'] if wisdom_summary else latest_summary['wisdom_summary'],
        'love_summary': love_summary['summary'] if love_summary else latest_summary['love_summary'],
        'metaculus_AGI_date': metaculus_AGI_date,
        'agi_questions_doc_id' : questions_doc_id,
        'agi_answers_doc_id' : answer_doc_id,
        'timestamp': firestore.SERVER_TIMESTAMP
    }, merge=True)

