from firebase_admin import firestore
from src.utils.db_init import db
from src.utils.helpers import get_latest_summary
from flask import Blueprint, render_template
from src.utils.helpers import category_inputs

love_blueprint = Blueprint('love_bp', __name__)

def get_love_inputs(limit=1):
    try:
        summary = get_latest_summary()
        # Reference to the 'daily_wisdom' collection, ordered by 'timestamp' descending
        love_ref = db.collection('love_understanding') \
                       .order_by('timestamp', direction=firestore.Query.DESCENDING) \
                       .limit(limit)
        
        docs = love_ref.stream()
        love_inputs = []
        for doc in docs:
            data = doc.to_dict()
            if 'timestamp' in data:
                data['timestamp'] = data['timestamp']
            love_inputs.append(data)

        return summary['love_summary'], love_inputs

    except Exception as e:
        print(f"Error retrieving wisdom: {e}")
        return []

@love_blueprint.route('/love_bp', endpoint='custom_love')
def love_page():
    love_headline, _ = get_love_inputs()
    love_inputs = category_inputs('love')
    print(f"Debug - Love Inputs: {love_inputs}")  # Add this line
    return render_template('index.html', page='love', love_headline=love_headline, love_inputs=love_inputs)

