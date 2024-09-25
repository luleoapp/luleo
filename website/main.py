import os
from src.qualia import get_latest_event
from dotenv import load_dotenv
from src.wisdom import get_wisdom
from src.love import get_love_inputs
from src.questions import get_questions
from src.agi import get_agi_predicted_date, get_days_to_agi, get_agi_answers
from flask import Flask, render_template, request, redirect, url_for, flash
from src.db_init import db, bucket
from firebase_admin import firestore
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Needed for flash messages


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Existing routes ...

@app.route("/contribute", methods=["GET", "POST"])
def contribute():
    if request.method == "POST":
        # Get form fields
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        analysis = request.form.get("analysis") == 'on'
        human = request.form.get("human") == 'on'
        ai = request.form.get("ai") == 'on'
        # Get the file from the form
        print(f"Debug - File: {request.files}")
        file = request.files.get("file") 
        doc = db.collection("user_inputs").document()
        upload_id = doc.id
        # Validate required fields
        if not name:
            flash("Name is required.", "error")
            return redirect(url_for('contribute'))
        
        file_url = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            blob = bucket.blob(f"user_uploads/{upload_id}_{filename}")
            blob.upload_from_file(file, content_type=file.content_type)
            blob.make_public()
            file_url = blob.public_url
            print(f"Uploaded file URL: {file_url}")
        elif file:
            flash("Invalid file type.", "error")
            return redirect(url_for('contribute'))

        # Prepare data to store
        data = {            
            "user_identity_str": name,
            "user_contact": email,
            "user_input_text": message,
            "show_me_the_analysis": analysis,
            "human": human,
            "ai": ai,
            "file_url": file_url,
            "timestamp": firestore.SERVER_TIMESTAMP
        }

        # Save to Firestore
        try:
            db.collection("user_inputs").document(upload_id).set(data)
            flash("Your message has been sent successfully!", "success")
        except Exception as e:
            print(f"Error saving to Firestore: {e}")
            flash("An error occurred while sending your message.", "error")
       
        return redirect(url_for('contribute', submitted=True, show_me_the_analysis=analysis))

    # Check if the form was submitted successfully
    submitted = request.args.get('submitted', False)

    if submitted:
        # Render a different template or pass a flag to display a success message
        return render_template('index.html', page='contribute', submitted=True)

    # For GET request without submission
    return render_template('index.html', page='contribute', submitted=False)

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
