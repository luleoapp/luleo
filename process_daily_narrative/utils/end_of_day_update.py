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
from utils.logger_config import upload_log_to_github

def get_processed_events(date_str=None):
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y%m%d').replace(tzinfo=PROJECT_TIMEZONE)
        except ValueError:
            logger.error(f"Invalid date format: {date_str}. Expected YYYYMMDD.")
            return []
    else:
        target_date = datetime.now(PROJECT_TIMEZONE)

    start_of_day = datetime.combine(target_date.date(), time.min).replace(tzinfo=PROJECT_TIMEZONE)
    end_of_day = datetime.combine(target_date.date(), time.max).replace(tzinfo=PROJECT_TIMEZONE)

    logger.info(f"Fetching events from {start_of_day} to {end_of_day}")    # Fetch all processed events from 'processed_events' collection for the target day
    docs = db.collection('processed_events') \
        .where('processed_at', '>=', start_of_day) \
        .where('processed_at', '<=', end_of_day) \
        .get()

    events = [doc.to_dict() for doc in docs]
    return events

def generate_end_of_day_update(events):
    # Prepare the summary of the day's events
    event_summaries = ["Summary: {0}\n, Emotion: {1}\n".format(event['summary'], event["qualia"]) for event in events if 'summary' in event and 'qualia' in event]
    event_details = "\n".join(event_summaries)
    logger.info("Num events: {0}".format(len(events)))
    logger.info(event_details)

    # Prepare the prompt
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    
    with open(os.path.join(prompts_dir, 'luleo.prompt'), 'r') as f:
        luleo_prompt = f.read()

    with open(os.path.join(prompts_dir, 'end_of_day_update.prompt'), 'r') as f:
        end_of_day_prompt_template = f.read()

    filled_prompt = end_of_day_prompt_template.replace('{{EVENT_DETAILS}}', event_details)

    client = OpenAI()

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": luleo_prompt},
                {"role": "user", "content": filled_prompt}
            ]
        )

        raw_response = completion.choices[0].message.content
        logger.info("Raw API Response:")
        logger.info(raw_response)

        # Extract the learning, wisdom, love, and questions
        learning_match = re.search(r'<learning>(.*?)</learning>', raw_response, re.DOTALL)
        wisdom_match = re.search(r'<wisdom>(.*?)</wisdom>', raw_response, re.DOTALL)
        love_match = re.search(r'<love>(.*?)</love>', raw_response, re.DOTALL)
        questions_match = re.search(r'<list_questions>(.*?)</list_questions>', raw_response, re.DOTALL)

        assert learning_match, "Learning not found in the response"
        assert wisdom_match, "Wisdom not found in the response"
        assert love_match, "Love understanding not found in the response"
        assert questions_match, "Questions not found in the response"

        learning = learning_match.group(1).strip()
        wisdom = wisdom_match.group(1).strip()
        love_understanding = love_match.group(1).strip()
        questions = re.findall(r'<question>(.*?)</question>', questions_match.group(1))

        assert learning, "Learning is empty"
        assert wisdom, "Wisdom is empty"
        assert love_understanding, "Love understanding is empty"
        assert len(questions) == 4, "Incorrect number of questions"

        return {
            "learning": learning,
            "wisdom": wisdom,
            "love_understanding": love_understanding,
            "questions": questions
        }

    except AssertionError as e:
        logger.error(f"Assertion failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error querying OpenAI API: {e}")
        return None

def store_functions(update_result, date_str=None):
    if not update_result:
        logger.error("No update result to store.")
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
        logger.info(f"Successfully stored end of day updates for {date_str}")
        
    except Exception as e:
        logger.error(f"Error storing end of day update in Firestore: {e}")

def update_end_of_day(date_str=None):
    events = get_processed_events(date_str)
    if not events:
        logger.info(f"No events to process for end of day update on {date_str if date_str else 'today'}.")
        return

    update_result = generate_end_of_day_update(events)
    if update_result is None:
        logger.error(f"Failed to generate end of day update for {date_str if date_str else 'today'}.")
        return

    # Store the update result in Firestore
    store_functions(update_result, date_str)

    return {"Success": True}