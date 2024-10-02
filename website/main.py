import os
from dotenv import load_dotenv
from src.routes.agi import get_agi_prediction_date
from flask import Flask, render_template
from src.routes.agi import agi_blueprint
from src.routes.contribute import contribute_blueprint
from src.routes.all_inputs import all_inputs_blueprint
from src.routes.analysis import analysis_blueprint
from src.routes.harmony import harmony_blueprint
from src.routes.questions import questions_blueprint
from src.routes.wisdom import wisdom_blueprint
from src.routes.love import love_blueprint
from src.routes.art import art_blueprint
from src.routes.divine import divine_blueprint
from src.routes.moloch import moloch_blueprint
from src.utils.helpers import get_latest_event
from src.routes.app_page import app_page_blueprint
from src.routes.agi import agi_blueprint
from src.routes.ideas import ideas_blueprint
load_dotenv()

app = Flask(__name__, template_folder='static/html')
app.secret_key = os.urandom(24)  # Needed for flash messages

app.register_blueprint(agi_blueprint)
app.register_blueprint(all_inputs_blueprint)
app.register_blueprint(analysis_blueprint)
app.register_blueprint(app_page_blueprint)
app.register_blueprint(art_blueprint)
app.register_blueprint(contribute_blueprint)
app.register_blueprint(divine_blueprint)
app.register_blueprint(ideas_blueprint)
app.register_blueprint(love_blueprint)
app.register_blueprint(moloch_blueprint)
app.register_blueprint(harmony_blueprint)
app.register_blueprint(questions_blueprint)
app.register_blueprint(wisdom_blueprint)

@app.route("/")
def index():
    image_url, summary, qualia = get_latest_event()
    _, days_to_agi = get_agi_prediction_date()
    spotify_playlist_uri = os.environ.get(
        'SPOTIFY_PLAYLIST_ID', 'spotify:playlist:5SCYMGXrvwRtlCe9sTC7m7')

    print(f"Debug - Image URL: {image_url}")  # Add this line
    print(f"Debug - Summary: {summary}")      # Add this line

    return render_template("index.html",page="home",
                           image_url=image_url,
                           spotify_playlist_uri=spotify_playlist_uri,
                           image_description=summary,
                           days_to_agi=days_to_agi)


if __name__ == "__main__":

    app.run(host="0.0.0.0", port=8080, debug=True)
