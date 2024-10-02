from flask import Blueprint, render_template

moloch_blueprint = Blueprint('moloch_bp', __name__)

@moloch_blueprint.route('/moloch', endpoint='custom_moloch')
def moloch():
    return render_template('index.html', page='moloch')

