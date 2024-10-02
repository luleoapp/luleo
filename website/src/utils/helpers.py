import json
import re
from src.utils.db_init import db, github_path
from firebase_admin import firestore


category_emojis = {
    'wisdom': "🧠",
    'love': "❤️",
    'ai': "🤖",
    'divine': "🙏",
    'app': "📱",
    'questions': "❓",
    'art': "🎨",
    'idea': "💡",
    'feedback': "💬",
    'miscellaneous': "🗂️",
    'spam': "🚫",
}

def get_category_emoji(category):
    return category_emojis.get(category, "🗂️")

def get_latest_summary():
    # Get the latest summary from the summary collection
    docs = db.collection("summary").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).get()
    if len(docs) == 0:
        return None
    return docs[0].to_dict()

def category_inputs(category, limits=10):
    query = db.collection("user_inputs").where(filter=firestore.FieldFilter("categories", "array_contains", category)).order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limits).stream()
    return [doc.to_dict() for doc in query]


def get_latest_event():
  query = (db.collection("qualia_updates")
           .where("image_path", "!=", "")
           .order_by("timestamp", direction=firestore.Query.DESCENDING)
           .limit(1))

  docs = query.get()

  if not docs:
      return None, None, None

  doc = docs[0].to_dict()
  github_file_path = github_path(doc.get("image_path"))
  return github_file_path, doc.get("summary"), doc.get("qualia")

def get_luleo_prompt():
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    # Read the Luleo system prompt
    with open(os.path.join(prompts_dir, 'luleo.prompt'), 'r') as f:
        base_prompt = f.read()  
    #add summary
    summary = get_latest_summary()
    prompt = base_prompt.replace("{{WISDOM_SUMMARY}}", summary['wisdom_summary']).replace("{{LOVE_SUMMARY}}", summary['love_summary'])
    return prompt


def clean_and_parse_json(raw_string):
    # Remove any leading/trailing whitespace
    raw_string = raw_string.strip()
    
    # Remove code block markers if present
    raw_string = re.sub(r'^```json\s*|\s*```$', '', raw_string, flags=re.MULTILINE)
    
    try:
        # Parse the JSON
        parsed_json = json.loads(raw_string)
        return parsed_json
    except json.JSONDecodeError as e:
        return f"Error parsing JSON: {str(e)}"
