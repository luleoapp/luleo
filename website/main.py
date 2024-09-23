from flask import Flask, render_template
import os
from src.qualia import get_latest_event
from dotenv import load_dotenv
from src.wisdom import get_wisdom
from src.love import get_love_inputs
from src.questions import get_questions
from src.agi import get_agi_predicted_date, get_days_to_agi, get_agi_answers
load_dotenv()

app = Flask(__name__)

@app.route('/agi')
def agi():
    prediction_date = get_agi_predicted_date()
    questions, answers, agi_vision_image_location = get_agi_answers()
    return render_template('index.html', page='agi', prediction_date=prediction_date, questions=questions, answers=answers, agi_vision_image_location=agi_vision_image_location)

@app.route('/wisdom')
def wisdom():
    #fetcch wisdom from firestore
    wisdom_headline, wisdom_quotes = get_wisdom()
    print(f"Debug - Wisdom Quotes: {wisdom_quotes}")  # Add this line
    # Add any wisdom-specific data here
    return render_template('index.html', page='wisdom', wisdom_headline=wisdom_headline, wisdom_quotes=wisdom_quotes)


@app.route('/love')
def love():
    #fetcch wisdom from firestore
    love_headline, love_inputs = get_love_inputs()
    print(f"Debug - Love Inputs: {love_inputs}")  # Add this line
    # Add any wisdom-specific data here
    return render_template('index.html', page='love', love_headline=love_headline, love_inputs=love_inputs)


@app.route('/questions')
def questions():
    #fetcch wisdom from firestore
    questions = get_questions()
    print(f"Debug - questions Inputs: {questions}")  # Add this line
    # Add any wisdom-specific data here
    return render_template('index.html', page='questions', questions=questions)



@app.route("/")
def index():
    image_url, summary, qualia = get_latest_event()
    days_to_agi = get_days_to_agi()
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
