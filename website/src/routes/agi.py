from firebase_admin import firestore
from datetime import datetime
import os, requests
from src.utils.db_init import db, github_path
from flask import Blueprint, render_template

agi_blueprint = Blueprint('agi_bp', __name__)

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
            print("Success: got metaculus data")
            json_val = response.json()
            last_prediction = json_val['simplified_history']['community_prediction'][-1]    
            predicted_date = last_prediction['val']
            return predicted_date
        else:
            print(f'Error {response.status_code}:', response.text)
            return None
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None

def get_agi_prediction_date():
    try:
        wisdom_ref = db.collection('summary') \
                        .order_by('timestamp', direction=firestore.Query.DESCENDING) \
                        .limit(1)
        doc = wisdom_ref.get()[0]
        data = doc.to_dict()
        metaculus_date = data['metaculus_AGI_date']
        
        predicted_date_str = metaculus_date
        today = datetime.now()
        predicted_date = datetime.strptime(predicted_date_str, '%b %d, %Y')
        days_to_agi = (predicted_date - today).days
        return predicted_date_str, days_to_agi
    except Exception as e:
        print(f"Error retrieving AGI prediction date: {e}")
        return None, None

def get_agi_answers():
    # Get the latest answer from the agi_questions collection
    doc = db.collection('agi_questions').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1).get()[0]
    data = doc.to_dict()
    answer_doc_id = data['latest_answer_doc_id']
    questions = data['questions']
    answers_doc = db.collection('agi_questions').document(doc.id).collection('answers').document(answer_doc_id).get().to_dict()
    answers = answers_doc['answers']
    if 'agi_vision_image' in answers_doc:
        agi_vision_image_location = github_path(answers_doc['agi_vision_image'])
    else:
        agi_vision_image_location = None
    return questions, answers, agi_vision_image_location

@agi_blueprint.route('/agi', endpoint="custom_agi")
def agi():
    prediction_date, _ = get_agi_prediction_date()
    questions, answers, agi_vision_image_location = get_agi_answers()
    return render_template('index.html', page='agi', prediction_date=prediction_date, questions=questions, answers=answers, agi_vision_image_location=agi_vision_image_location)

