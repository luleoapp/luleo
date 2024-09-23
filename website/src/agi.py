import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os
from src.db_init import db, github_path
from src.luleo import get_latest_summary

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


def get_days_to_agi():
    predicted_date = get_agi_predicted_date()
    today = datetime.now()
    predicted_date = datetime.strptime(predicted_date, '%b %d, %Y')
    days_to_agi = (predicted_date - today).days
    return days_to_agi

def get_agi_answers():
    # Get the latest answer from the agi_questions collection
    doc = db.collection('agi_questions').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(1).get()[0]
    data = doc.to_dict()
    answer_doc_id = data['latest_answer_doc_id']
    questions = data['questions']
    answers_doc = db.collection('agi_questions').document(doc.id).collection('answers').document(answer_doc_id).get().to_dict()
    answers = answers_doc['answers']
    agi_vision_image_location = github_path(answers_doc['agi_vision_image'])
    return questions, answers, agi_vision_image_location