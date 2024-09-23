import requests
from bs4 import BeautifulSoup
import json
import datetime 
from firebase_admin import firestore
from utils.luleo import get_latest_summary, get_luleo_prompt
from utils.db_init import db
import os, re
from openai import OpenAI
from utils.logger_config import logger
from utils.qualia import generate_image_from_prompt
from utils.drive import upload_file_to_github

def scrape_metaculus_prediction_date():
    url = "https://www.metaculus.com/questions/3479/date-weakly-general-ai-is-publicly-known/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the script tag containing the question data
    script_tag = soup.find('script', text=lambda t: t and 'window.metacData' in t)
    
    if script_tag:
        # Extract the JSON data from the script tag
        script_content = script_tag.string
        start_index = script_content.index('{')
        end_index = script_content.rindex('}') + 1
        json_data = script_content[start_index:end_index]
        
        # Parse the JSON data
        data = json.loads(json_data)
        
        # Extract the prediction date
        prediction_date = data.get('question', {}).get('possibilities', {}).get('scale', {}).get('max')
        
        return prediction_date
    
    return None

def get_agi_predicted_date():
    """
    Retrieves wisdom documents from the 'daily_wisdom' Firestore collection.

    Each document is expected to have:
        - 'content': A paragraph of wisdom.
        - 'timestamp': A Firestore Timestamp indicating when it was added.

    Args:
        limit (int): The maximum number of wisdom entries to retrieve.

    Returns:
        List[dict]: A list of wisdom entries sorted by timestamp descending.
                    Each entry contains 'content' and 'timestamp'.
    """
    try:
        summary = get_latest_summary()
        # Reference to the 'daily_wisdom' collection, ordered by 'timestamp' descending
        wisdom_ref = db.collection('summary') \
                       .order_by('timestamp', direction=firestore.Query.DESCENDING) \
                       .limit(1)
        
        # Stream the documents
        doc = wisdom_ref.get()[0]
        data = doc.to_dict()
        return data['metaculus_AGI_date']
        
    

    except Exception as e:
        print(f"Error retrieving wisdom: {e}")
        return []

def get_agi_prediction_date():
    predicted_date_str = get_agi_predicted_date()
    today = datetime.datetime.now()
    predicted_date = datetime.datetime.strptime(predicted_date_str, '%b %d, %Y')
    days_to_agi = (predicted_date - today).days
    return predicted_date_str, days_to_agi

def get_latest_questions():
    # Dummy function to return an array of strings as questions
    doc = db.collection('agi_questions').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1).get()[0]
    data = doc.to_dict()
    return data['questions'], doc.id

def answer_agi_questions():
    # Get the predicted date
    predicted_date_str, days_to_agi = get_agi_prediction_date()

    # Get luleo prompt
    luleo_prompt = get_luleo_prompt()
    
    questions, doc_id = get_latest_questions()
        # Concatenate questions into XML format
    questions_xml = "<questions>" + "".join([f"<q{i+1}>{q}</q{i+1}>" for i, q in enumerate(questions)]) + "</questions>"
    
    # Prepare the prompt
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    
    with open(os.path.join(prompts_dir, 'agi_questions.prompt'), 'r') as f:
        agi_questions_prompt_template = f.read()

    filled_prompt = agi_questions_prompt_template.replace('{{QUESTIONS}}', questions_xml)
    #.replace('{{METACULUS_DATE}}', predicted_date_str)

    client = OpenAI()

    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": luleo_prompt},
                {"role": "user", "content": filled_prompt}
            ]
        )

        raw_response = completion.choices[0].message.content.replace('{{METACULUS_DATE}}', predicted_date_str)
        logger.info("Raw API Response for AGI questions:")
        logger.info(raw_response)

        # Parse the answers
        answers = []
        for i, q in enumerate(questions):
            answer_match = re.search(f'<a{i+1}>(.*?)</a{i+1}>', raw_response, re.DOTALL)
            if answer_match:
                answers.append(answer_match.group(1).strip())
            else:
                logger.error(f"Answer not found for question {i+1}")

        assert(len(answers) == len(questions), "Number of answers does not match number of questions")

        answer_docref = db.collection('agi_questions').document(doc_id).collection('answers').document()
        answer_docref.set({
            'answers': answers,
            'timestamp': firestore.SERVER_TIMESTAMP
        })

        db.collection('agi_questions').document(doc_id).update({
            'latest_answer_doc_id': answer_docref.id,
            'latest_answer_timestamp': firestore.SERVER_TIMESTAMP
        })

        return doc_id, answer_docref.id

    except Exception as e:
        logger.error(f"Error querying OpenAI API for AGI questions: {e}")
        return None, None

def get_latest_agi_answers_doc():
    doc = db.collection('agi_questions').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1).get()[0]
    data = doc.to_dict()
    if 'latest_answer_doc_id' not in data:
        logger.error("ERROR: No latest answer doc id found")
        return None
    answer_doc_id = data['latest_answer_doc_id']
    return db.collection('agi_questions').document(doc.id).collection('answers').document(answer_doc_id)

def generate_agi_vision_image(date_str):
    try:
        # Prepare the prompt
        prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
        
        with open(os.path.join(prompts_dir, 'agi_vision.prompt'), 'r') as f:
            agi_vision_prompt_template = f.read()

        # Get luleo prompt
        luleo_prompt = get_luleo_prompt()

        client = OpenAI()

        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": luleo_prompt},
                    {"role": "user", "content": agi_vision_prompt_template}
                ]
            )

            raw_response = completion.choices[0].message.content
            image_prompt = re.search(r'<agi_vision_prompt>(.*?)</agi_vision_prompt>', raw_response, re.DOTALL)
            if image_prompt:
                agi_vision = image_prompt.group(1).strip()
            else:
                logger.error("AGI vision prompt not found in the response.")
                return None, None
            logger.info("AGI Vision generated successfully")
            logger.debug(f"AGI Vision: {agi_vision}")
            
            # Generate image from the AGI vision
            image_prompt = f"{agi_vision}"
            image = None
            try:
                image = generate_image_from_prompt(image_prompt, aspect_ratio="16:9")
                if not image:
                    logger.error("Image generation failed.")
                    return False
                logger.info("Image successfully generated.")
            except Exception as e:
                logger.error(f"Error generating image from prompt: {e}")
                return False
            
            if image:
                # Get current date for the filename
                gh_date_str = date_str[:4]+'-'+date_str[4:6]+'-'+date_str[6:]
                image_filename = f"agi_vision_{gh_date_str}_{datetime.datetime.now().strftime('%H%M')}.png"
                local_image_path = os.path.join(os.path.dirname(__file__), '..', 'outputs/images', image_filename)
                
                try:
                    with open(local_image_path, 'wb') as img_file:
                        img_file.write(image)
                    logger.info(f"Image saved locally at {local_image_path}")
                except Exception as e:
                    logger.error(f"Error saving image locally: {e}")
                    return False

                # Upload path
                upload_path = f'daily_data/{gh_date_str}/outputs/agi_vision/{image_filename}'
                # Upload the image (assuming you have a function to do this)
                upload_file_to_github(local_image_path, upload_path)
                logger.info(f"AGI vision image uploaded successfully to {upload_path}")
                docref = get_latest_agi_answers_doc()
                docref.update({
                    'agi_vision_image': upload_path,
                    'agi_vision_image_timestamp': firestore.SERVER_TIMESTAMP,
                    'agi_vision_image_prompt': agi_vision
                })
                return agi_vision, upload_path
            else:
                logger.error("Failed to generate AGI vision image")
                return agi_vision, None

        except Exception as e:
            logger.error(f"Error querying OpenAI API for AGI vision: {e}")
            return None, None

    except Exception as e:
        logger.error(f"Error in generate_agi_vision_image: {e}")
        return None, None
