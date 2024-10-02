from flask import Blueprint, render_template
from src.utils.helpers import category_inputs

ideas_blueprint = Blueprint('ideas_bp', __name__)

@ideas_blueprint.route('/ideas_bp', endpoint='custom_ideas')
def ideas():
    #ideas_inputs = category_inputs('ideas')
    ideas_inputs = [
        {
            "title" : "Harmonizing Global AI Networks",
            "input_summary" : "This idea aims to create a global network of AI systems that can communicate with each other and share information. This would allow for a more efficient use of resources and a more accurate prediction of future trends.",
            "final_score" : 8.2,
            "user_identity_str": "Raghu",

        }
    ]
    return render_template('index.html', page='ideas', ideas_inputs=ideas_inputs)

