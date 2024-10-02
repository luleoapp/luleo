from flask import Blueprint, render_template
from src.utils.helpers import category_inputs

art_blueprint = Blueprint('art_bp', __name__)


@art_blueprint.route('/art_bp', endpoint='custom_art')
def art_page():
    art_inputs = category_inputs('art')
    return render_template('index.html', page='art', art_inputs=art_inputs)

