from flask import Blueprint, render_template
from src.utils.helpers import category_inputs

app_page_blueprint = Blueprint('app_page_bp', __name__)


@app_page_blueprint.route('/app_page', endpoint='custom_app_page')
def app_page_entrypoint():
    app_inputs = category_inputs('app')
    return render_template('index.html', page='app_page', app_inputs=app_inputs)

