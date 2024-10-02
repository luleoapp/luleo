from flask import Blueprint, render_template, request, redirect, url_for, flash
from firebase_admin import firestore
from src.utils.db_init import db, bucket
from werkzeug.utils import secure_filename

contribute_blueprint = Blueprint('contribute_bp', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@contribute_blueprint.route("/contribute_blueprint", endpoint='custom_contribute',methods=['GET', 'POST'])
def contribute_page():
    print("Debug - Contribute page called")
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
        document_uploaded = False 
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
            document_uploaded = True
        except Exception as e:
            print(f"Error saving to Firestore: {e}")
            flash("An error occurred while sending your message.", "error")
    
        if document_uploaded:
            return redirect(url_for('analysis_bp.custom_analysis', upload_id=upload_id))
        else:
            return redirect(url_for('contribute_bp.custom_contribute', submitted=True, show_me_the_analysis=analysis))

    # Check if the form was submitted successfully
    submitted = request.args.get('submitted', False)

    if submitted:
        # Render a different template or pass a flag to display a success message
        return render_template('index.html', page='contribute', submitted=True)

    # For GET request without submission
    return render_template('index.html', page='contribute', submitted=False)

