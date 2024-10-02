from flask import Blueprint, render_template
from firebase_admin import firestore
from src.utils.db_init import db
from src.utils.helpers import get_category_emoji

all_inputs_blueprint = Blueprint('all_inputs_bp', __name__)


@all_inputs_blueprint.route('/all_inputs_bp', endpoint='custom_all_inputs')
def all_inputs_page():
    docs = db.collection("user_inputs").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(10).stream()
    data = [doc.to_dict() for doc in docs]
    for item in data:
        item['categories_str'] = "".join([get_category_emoji(category) for category in item.get('categories', [])])
    return render_template('index.html', page='all_inputs', data=data)


