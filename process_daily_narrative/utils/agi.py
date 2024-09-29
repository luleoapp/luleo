import requests
import datetime 
from firebase_admin import firestore
from utils import llm_utils
from utils.luleo import get_luleo_prompt
from utils.db_init import db
import os
from utils.logger_config import system_logger
from utils.qualia import generate_image_from_prompt
from utils.drive import upload_file_to_github

def scrape_metaculus_prediction_date():
    try:
        url = f'https://www.metaculus.com/api2/questions/3479'
        headers = {
            'Authorization': f'Token {os.environ.get("METACULUS_TOKEN")}',
            'Content-Type': 'application/json'
        }
        data = {}
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            system_logger.info("Success: got metaculus data")
            json_val = response.json()
            last_prediction = json_val['simplified_history']['community_prediction'][-1]    
            predicted_date = last_prediction['val']
            return predicted_date
        else:
            system_logger.error(f'Error {response.status_code}:', response.text)
            return None
    except Exception as e:
        system_logger.error(f"An error occurred: {str(e)}")
        return None

def get_agi_prediction_date():
    try:
        metaculus_date = scrape_metaculus_prediction_date()
        if not metaculus_date:
            wisdom_ref = db.collection('summary') \
                           .order_by('timestamp', direction=firestore.Query.DESCENDING) \
                           .limit(1)
            doc = wisdom_ref.get()[0]
            data = doc.to_dict()
            metaculus_date = data['metaculus_AGI_date']
        
        predicted_date_str = metaculus_date
        today = datetime.datetime.now()
        predicted_date = datetime.datetime.strptime(predicted_date_str, '%b %d, %Y')
        days_to_agi = (predicted_date - today).days
        return predicted_date_str, days_to_agi
    except Exception as e:
        system_logger.error(f"Error retrieving AGI prediction date: {e}")
        return None, None

def get_latest_questions():
    # Dummy function to return an array of strings as questions
    doc = db.collection('agi_questions').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1).get()[0]
    data = doc.to_dict()
    return data['questions'], doc.id

def answer_agi_questions():
    # Get the predicted date
    predicted_date_str, _ = get_agi_prediction_date()

    # Get luleo prompt
    luleo_prompt = get_luleo_prompt()
    
    questions, doc_id = get_latest_questions()
    # Concatenate questions into XML format
    questions_xml = "<questions>" + "".join([f"<q{i+1}>{q}</q{i+1}>" for i, q in enumerate(questions)]) + "</questions>"
    
    # Prepare the prompt
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    
    with open(os.path.join(prompts_dir, 'agi_questions.prompt'), 'r') as f:
        agi_questions_prompt_template = f.read()

    filled_prompt = agi_questions_prompt_template.replace('{{QUESTIONS}}', questions_xml).replace('{{METACULUS_DATE}}', predicted_date_str)


    try:
        response_json = llm_utils.call_and_log_llm(system_prompt=luleo_prompt, user_prompt=filled_prompt, model="gpt-4o")
        answers = response_json.get("answers")

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
        system_logger.error(f"Error querying OpenAI API for AGI questions: {e}")
        return None, None

def get_latest_agi_answers_doc():
    doc = db.collection('agi_questions').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1).get()[0]
    data = doc.to_dict()
    if 'latest_answer_doc_id' not in data:
        system_logger.error("ERROR: No latest answer doc id found")
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


        try:
            response_json = llm_utils.call_and_log_llm(system_prompt=luleo_prompt, user_prompt=agi_vision_prompt_template, model="gpt-4o-mini")
            image_prompt = response_json.get("agi_vision_prompt")
            image = None
            try:
                image = generate_image_from_prompt(image_prompt, aspect_ratio="16:9")
                if not image:
                    system_logger.error("Image generation failed.")
                    return False
                system_logger.info("Image successfully generated.")
            except Exception as e:
                system_logger.error(f"Error generating image from prompt: {e}")
                return False
            
            if image:
                # Get current date for the filename
                gh_date_str = date_str[:4]+'-'+date_str[4:6]+'-'+date_str[6:]
                image_filename = f"agi_vision_{gh_date_str}_{datetime.datetime.now().strftime('%H%M')}.png"
                local_image_path = os.path.join(os.path.dirname(__file__), '..', 'outputs/images', image_filename)
                
                try:
                    with open(local_image_path, 'wb') as img_file:
                        img_file.write(image)
                    system_logger.info(f"Image saved locally at {local_image_path}")
                except Exception as e:
                    system_logger.error(f"Error saving image locally: {e}")
                    return False

                # Upload path
                upload_path = f'daily_data/{gh_date_str}/outputs/agi_vision/{image_filename}'
                # Upload the image (assuming you have a function to do this)
                upload_file_to_github(local_image_path, upload_path)
                system_logger.info(f"AGI vision image uploaded successfully to {upload_path}")
                docref = get_latest_agi_answers_doc()
                docref.update({
                    'agi_vision_image': upload_path,
                    'agi_vision_image_timestamp': firestore.SERVER_TIMESTAMP,
                    'agi_vision_image_prompt': image_prompt
                })
                return image_prompt, upload_path
            else:
                system_logger.error("Failed to generate AGI vision image")
                return image_prompt, None

        except Exception as e:
            system_logger.error(f"Error querying OpenAI API for AGI vision: {e}")
            return None, None

    except Exception as e:
        system_logger.error(f"Error in generate_agi_vision_image: {e}")
        return None, None
