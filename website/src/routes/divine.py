from flask import Blueprint, render_template
from src.utils.helpers import category_inputs

divine_blueprint = Blueprint('divine_bp', __name__)


@divine_blueprint.route('/divine_bp', endpoint='custom_divine')
def divine_page():
    #divine_inputs = category_inputs('divine')
    divine_inputs = [
        {
            'title': 'Your Divine Title',
            'description': 'Your two-line description goes here. It will be truncated if it exceeds two lines on any screen size.',
            'link': 'https://github.com/luleoapp/luleo'
        }
    ]
    return render_template('index.html', page='divine', divine_inputs=divine_inputs)


