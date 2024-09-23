import json
import os
from openai import OpenAI
import re, math
from datetime import datetime, time
from utils.db_init import db, PROJECT_TIMEZONE
from google.cloud.firestore_v1 import aggregation
from google.cloud.firestore_v1.base_query import FieldFilter
from random import shuffle
from utils.spotify import add_to_spotify_playlist
from google.cloud import firestore
from utils.logger_config import logger
from utils.drive import upload_file_to_github
import io
from replicate.client import Client
import requests
import tempfile
import os

def get_default_panas():
    return {
        "positive_affect": {
            "total_score": 0,
            "items": {
                "interested": 0,
                "excited": 0,
                "strong": 0,
                "enthusiastic": 0,
                "proud": 0,
                "alert": 0,
                "inspired": 0,
                "determined": 0,
                "attentive": 0,
                "active": 0
            }
        },
        "negative_affect": {
            "total_score": 0,
            "items": {
                "distressed": 0,
                "upset": 0,
                "guilty": 0,
                "scared": 0,
                "hostile": 0,
                "irritable": 0,
                "ashamed": 0,
                "nervous": 0,
                "jittery": 0,
                "afraid": 0
            }
        }
    }

def get_emotional_response(event_type, event_details, current_panas=None):
    if current_panas is None:
        current_panas = get_default_panas()
    
    current_panas_str = json.dumps(current_panas, indent=2)

    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    
    with open(os.path.join(prompts_dir, 'get_qualia.prompt'), 'r') as f:
        get_qualia_prompt = f.read()
    
    from utils.luleo import get_luleo_prompt
    luleo_prompt = get_luleo_prompt()
    
    filled_prompt = get_qualia_prompt.replace('{{CURRENT_PANAS}}', current_panas_str).replace('{{EVENT_TYPE}}', event_type).replace('{{EVENT_DETAILS}}', event_details)
    
    client = OpenAI()
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": luleo_prompt},
                {"role": "user", "content": filled_prompt}
            ]
        )
        
        raw_response = completion.choices[0].message.content
        logger.info("Raw API Response:")
        logger.info(raw_response)
        
        panas_match = re.search(r'<updated_panas>(.*?)</updated_panas>', raw_response, re.DOTALL)
        summary_match = re.search(r'<summary>(.*?)</summary>', raw_response, re.DOTALL)
        qualia_match = re.search(r'<qualia>(.*?)</qualia>', raw_response, re.DOTALL)
        image_prompt_match = re.search(r'<image_prompt>(.*?)</image_prompt>', raw_response, re.DOTALL)
        
        # Add assertions to ensure all required fields are present
        assert panas_match, "Updated PANAS not found in the response"
        assert summary_match, "Summary not found in the response"
        assert qualia_match, "Qualia not found in the response"
        assert image_prompt_match, "Image prompt not found in the response"
        
        panas_json_str = panas_match.group(1).strip()
        summary = summary_match.group(1).strip()
        qualia = qualia_match.group(1).strip()
        image_prompt = image_prompt_match.group(1).strip()
        
        # Add assertions to ensure fields are not empty
        assert summary, "Summary is empty"
        assert qualia, "Qualia is empty"
        assert image_prompt, "Image prompt is empty"
        
        try:
            updated_panas = json.loads(panas_json_str)
            logger.info("Processed Updated PANAS:")
            logger.info(json.dumps(updated_panas, indent=2))
            
            return {
                "updated_panas": updated_panas,
                "summary": summary,
                "qualia": qualia,
                "image_prompt": image_prompt
            }
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding PANAS JSON: {e}")
            return None
    
    except AssertionError as e:
        logger.error(f"Assertion failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error querying OpenAI API: {e}")
        return None

def get_event_types():
    return {
        'daily' : [
            'retrieved_reddit_posts',
            'retrieved_articles',
        ],
        'hourly': [
            'ideas',
            'daily_updates',
            'feedback'
        ],
    }

def get_events_to_process():
    event_types = get_event_types()
    daily_events = event_types['daily']
    hourly_events = event_types['hourly']

    current_datetime = datetime.now(PROJECT_TIMEZONE)
    current_date = current_datetime.date()
    
    # Create a timezone-aware datetime for the end of the day
    end_of_day = datetime.combine(current_date, time.max).replace(tzinfo=PROJECT_TIMEZONE)
    
    # Calculate the hours left
    hours_left = (end_of_day - current_datetime).total_seconds() / 3600
    
    all_events = []
    for event_type in daily_events:
        query = db.collection(event_type).where(filter=FieldFilter("processed_for_qualia", "==", False))
        number_of_events_to_process = None 

        if hours_left > 1:
            aggregate_query = aggregation.AggregationQuery(query)
            aggregate_query.count(alias="unprocessed_count")
            results = list(aggregate_query.get())
            if results:
                logger.info(results)
                number_of_unprocessed_events = results[0][0].value
                number_of_events_to_process = math.ceil(number_of_unprocessed_events / hours_left)
                query = query.limit(number_of_events_to_process)
                logger.info(f"Processing {number_of_events_to_process} out of {number_of_unprocessed_events} events for {event_type}")
            else:
                logger.info(f"No unprocessed events found for {event_type}")
                continue

        
        docs = query.get()
        assert(number_of_events_to_process is None or len(docs) == number_of_events_to_process)
        for doc in docs:
            all_events.append({'event_dict': doc.to_dict(), 'event_type': event_type, 'event_id': doc.id})
    
    for event_type in hourly_events:
        query = db.collection(event_type).where(filter=FieldFilter("processed_for_qualia", "==", False))
        docs = query.get()
        for doc in docs:
            all_events.append({'event_dict': doc.to_dict(), 'event_type': event_type, 'event_id': doc.id})
    
    return all_events

def get_current_emotional_state():
    docs = db.collection('qualia_updates').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1).get()
    if len(docs) == 0:
        return get_default_panas()
    else:
        doc_dict = docs[0].to_dict()
        return doc_dict['updated_panas']

def update_processed_event(event, d_ret):
    d_doc = event['event_dict']
    d_doc.pop('processed_for_qualia', None)
    d_doc.pop('qualia_event_id', None)
    d_doc.update(d_ret) 
    d_doc['event_type'] = event['event_type']
    d_doc['processed_at'] = datetime.now(PROJECT_TIMEZONE)  # Add this line
    d_doc["event_id"] = event['event_id']
    _, event_doc = db.collection('processed_events').add(d_doc)

    db.collection(event['event_type']).document(event['event_id']).update({
        'processed_for_qualia': True,
        'qualia_event_id': event_doc.id,
        'processed_at': firestore.SERVER_TIMESTAMP  # Add this line
    })

def generate_image_from_prompt(image_prompt, aspect_ratio=None):
    try:
        replicate = Client(api_token=os.environ['REPLICATE_API_TOKEN'])

        logger.info(f"Generating image with prompt: {image_prompt} and aspect ratio: {aspect_ratio if aspect_ratio is not None else '1:1'}")
        input_dict = {"prompt": image_prompt}
        if aspect_ratio is not None:
            input_dict["aspect_ratio"] = aspect_ratio
        output = replicate.run(
            "black-forest-labs/flux-pro",
            input=input_dict,
        )
        
        if not output:
            logger.error("Failed to generate image: Empty output from Replicate API")
            return None

        image_url = output
        logger.info(f"Image generated successfully. URL: {image_url}")

        logger.info(f"Downloading image from URL: {image_url}")
        response = requests.get(image_url)
        if response.status_code != 200:
            logger.error(f"Failed to download image: HTTP status code {response.status_code}")
            return None

        return response.content

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while downloading image: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error generating image: {str(e)}")
    
    return None



def process_and_upload_image(image_prompt, event_id, qualia_doc_id):
    image_content = generate_image_from_prompt(image_prompt)
    if image_content is None:
        return None

    curr_dt = datetime.now(PROJECT_TIMEZONE).strftime("%Y-%m-%d")
    current_time = datetime.now(PROJECT_TIMEZONE).strftime("%H%M")
    filename = f"event_id_{event_id}_{current_time}.webp"
    file_path = f"daily_data/{curr_dt}/outputs/{filename}"
    logger.info(f"Generated file path: {file_path}")

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.webp') as temp_file:
        temp_file.write(image_content)
        temp_file_path = temp_file.name

    try:
        # Upload to GitHub using the function from drive.py
        logger.info(f"Uploading image to GitHub: {file_path}")
        upload_result = upload_file_to_github(temp_file_path, file_path)

        if 'message' in upload_result:
            github_url = file_path  # or construct the full GitHub URL if needed
            logger.info(f"Image uploaded successfully. URL: {github_url}")

            # Update the qualia_updates document with the image path
            logger.info(f"Updating qualia_updates document {qualia_doc_id} with image path")
            db.collection('qualia_updates').document(qualia_doc_id).update({
                'image_path': github_url
            })

            return github_url
        else:
            logger.error(f"Failed to upload image to GitHub for event {event_id}: {upload_result.get('error', 'Unknown error')}")
            return None
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_path)

    return None
def update_qualia():
    events_to_process = get_events_to_process()
    shuffle(events_to_process)
    current_emotional_state = get_current_emotional_state()
    max_significance_event = None
    max_significance = -1
    logger.info(f"Events to process: {len(events_to_process)}")
    num_events_considered_by_type = {}

    # Calculate initial positive-negative score
    initial_pn_score = (
        current_emotional_state['positive_affect']['total_score'] -
        current_emotional_state['negative_affect']['total_score']
    )

    for event in events_to_process:
        assert('summary' in event['event_dict'])
        event_details = event['event_dict']['summary']
        num_events_considered_by_type[event['event_type']] = num_events_considered_by_type.get(event['event_type'], 0) + 1
        d_ret = get_emotional_response(event['event_type'], event_details, current_emotional_state)
        if d_ret is not None:
            update_processed_event(event, d_ret)
            
            # Calculate new positive-negative score
            new_pn_score = (
                d_ret['updated_panas']['positive_affect']['total_score'] -
                d_ret['updated_panas']['negative_affect']['total_score']
            )
            
            # Calculate change in positive-negative score
            pn_score_change = abs(new_pn_score - initial_pn_score)
            
            if max_significance_event is None or pn_score_change > max_significance:
                max_significance = pn_score_change
                max_significance_event = (event, d_ret)

    if max_significance_event is None:
        logger.error(f"ERROR : No significant event found at {datetime.now(PROJECT_TIMEZONE)}")
        return 
    else:
        logger.info(f"Max significance event: {max_significance_event}")
        result, track_id, track_name, artist_name = add_to_spotify_playlist(max_significance_event[1]['updated_panas'])

        # Add the document to Firestore and get the document ID
        doc_ref = db.collection('qualia_updates').add({
            'timestamp': datetime.now(PROJECT_TIMEZONE),
            'events_considered' : num_events_considered_by_type,
            'event_id': max_significance_event[0]['event_id'],
            'event_type': max_significance_event[0]['event_type'],
            'event_details': max_significance_event[0]['event_dict']['summary'],
            'updated_panas': max_significance_event[1]['updated_panas'],
            'summary': max_significance_event[1]['summary'],
            'qualia': max_significance_event[1]['qualia'],
            'spotify_track_id': track_id,
            'spotify_track_name': track_name,
            'spotify_artist_name': artist_name,
            'significance_score': max_significance,
            'image_prompt': max_significance_event[1]['image_prompt'],
            'image_path': ''  # Initialize with empty string
        })
        qualia_doc_id = doc_ref[1].id

        # Generate and upload the image
        image_path = process_and_upload_image(max_significance_event[1]['image_prompt'], max_significance_event[0]['event_id'], qualia_doc_id)
        
        if image_path:
            logger.info(f"Image generated and uploaded successfully: {image_path}")
        else:
            logger.warning("Failed to generate or upload image")

        logger.info(result)



