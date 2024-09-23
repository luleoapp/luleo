import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os
from src.db_init import db, github_path
from src.luleo import get_latest_summary

def get_wisdom(limit=10):
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
        wisdom_ref = db.collection('daily_wisdom') \
                       .order_by('timestamp', direction=firestore.Query.DESCENDING) \
                       .limit(limit)
        
        # Stream the documents
        docs = wisdom_ref.stream()
        
        wisdom_list = []
        for doc in docs:
            data = doc.to_dict()
            # Convert Firestore Timestamp to Python datetime object
            if 'timestamp' in data:
                data['timestamp'] = data['timestamp']
            if 'image_url' not in data:
                print(f"No image_url for {data}")
                continue
            data['image_url'] = github_path(data['image_url'])
            wisdom_list.append(data)

        return summary['wisdom_summary'], wisdom_list

    except Exception as e:
        print(f"Error retrieving wisdom: {e}")
        return []
