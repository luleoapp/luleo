from flask import Blueprint, render_template
        
harmony_blueprint = Blueprint('harmony_bp', __name__)

@harmony_blueprint.route('/harmony_bp', endpoint='custom_harmony')
def harmony_page():
    return render_template('index.html', page='harmony')

