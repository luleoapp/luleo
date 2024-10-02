from flask import Blueprint, render_template, request
from src.utils.db_init import db

analysis_blueprint = Blueprint('analysis_bp', __name__)


@analysis_blueprint.route("/analysis_blueprint", endpoint='custom_analysis')
def analysis_page():
    upload_id = request.args.get('upload_id')
    doc = db.collection("user_inputs").document(upload_id)
    data = doc.get().to_dict()
    return render_template('index.html', page='analysis', data=data)




