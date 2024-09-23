import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os
from src.db_init import db, github_path


def get_questions(limit=10):
    try:
        # Reference to the 'daily_wisdom' collection, ordered by 'timestamp' descending
        love_ref = db.collection('end_of_day_questions') \
                       .order_by('timestamp', direction=firestore.Query.DESCENDING) \
                       .limit(limit)
        
        # Stream the documents
        docs = love_ref.stream()
        
        love_inputs = []
        for doc in docs:
            data = doc.to_dict()
            # Convert Firestore Timestamp to Python datetime object
            if 'timestamp' in data:
                data['timestamp'] = data['timestamp']
            love_inputs.append(data)

        return love_inputs

    except Exception as e:
        print(f"Error retrieving wisdom: {e}")
        return []
