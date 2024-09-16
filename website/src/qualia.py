from src.db_init import db
from firebase_admin import firestore
def get_latest_event():
  query = (db.collection("qualia_updates")
           .where("image_path", "!=", "")
           .order_by("timestamp", direction=firestore.Query.DESCENDING)
           .limit(1))

  docs = query.get()

  if not docs:
      return None, None, None

  doc = docs[0].to_dict()
  github_file_path = "https://raw.githubusercontent.com/luleoapp/luleo/main/"+doc.get("image_path")
  return github_file_path, doc.get("summary"), doc.get("qualia")