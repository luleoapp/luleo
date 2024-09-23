from src.db_init import db
from firebase_admin import firestore


def get_latest_summary():
    # Get the latest summary from the summary collection
    docs = db.collection("summary").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).get()
    if len(docs) == 0:
        return None
    return docs[0].to_dict()

