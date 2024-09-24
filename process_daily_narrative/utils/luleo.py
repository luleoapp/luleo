import os 
import tempfile
from utils.db_init import db
from utils.logger_config import logger
from firebase_admin import firestore
from openai import OpenAI
import re
from utils.drive import upload_file_to_github, get_user_input_document_path
from utils.drive import full_github_resource_path
import requests
from urllib.parse import urlparse
import os


def get_luleo_prompt():
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    # Read the Luleo system prompt
    with open(os.path.join(prompts_dir, 'luleo.prompt'), 'r') as f:
        base_prompt = f.read()  
    #add summary
    summary = get_latest_summary()
    prompt = base_prompt.replace("{{WISDOM_SUMMARY}}", summary['wisdom_summary']).replace("{{LOVE_SUMMARY}}", summary['love_summary'])
    return prompt


def process_user_upload(upload_id):
    doc = db.collection("user_inputs").document(upload_id).get()
    if not doc.exists:
        logger.error(f"ERROR : User input document {upload_id} does not exist")
        return None
    data = doc.to_dict()
    user_identity_str = data.get("name")
    user_input_text = data.get("message")
    user_input_image_path = data.get("file_url")
    # Download the image from Firebase storage to a local file
    if user_input_image_path:
        try:
            # Parse the URL to get the filename
            parsed_url = urlparse(user_input_image_path)
            filename = os.path.basename(parsed_url.path)
            # Create a temporary file to store the downloaded image
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
                # Download the image
                response = requests.get(user_input_image_path)
                response.raise_for_status()  # Raise an exception for bad status codes
                
                # Write the content to the temporary file
                temp_file.write(response.content)
                
                # Store the path of the temporary file
                local_image_path = temp_file.name

            logger.info(f"Image downloaded successfully to {local_image_path}")
            
            # Update user_input_image_path to the local file path
            user_input_image_path = local_image_path
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            user_input_image_path = None
    return classify_user_input(upload_id, user_identity_str, user_input_text, user_input_image_path)


def classify_user_input(upload_id, user_identity_str, user_input_text=None, user_input_image_path=None):
    #if both are none, return None
    if user_input_text is None and user_input_image_path is None:
        logger.error("No user input provided")
        return None
    
    gh_file_dir = get_user_input_document_path(upload_id)
    gh_image_path = None
    image_input_dict = None 
    #upload image to github
    if user_input_image_path:
        #todo : get local file path of image
        image_filename = os.path.basename(user_input_image_path)
        gh_image_path = f'{gh_file_dir}/{image_filename}'
        msg = upload_file_to_github(user_input_image_path, gh_image_path)
        if 'error' in msg:
            logger.error(f"Error uploading image to GitHub: {msg}")
            gh_image_path = None
        else:
            image_input_dict = {
                "type" : "image_url",
                "image_url" : {
                    "url" : full_github_resource_path(gh_image_path)
                }
            }
    #upload identity and text to github
    _, tmpf = tempfile.mkstemp(suffix='.xml')
    
    with open(tmpf, 'w') as f:
        f.write(f'<user_identity>{user_identity_str}</user_identity>\n')
        if user_input_text:
            f.write(f'<user_input>{user_input_text}</user_input>')

    input_file_path = f'{gh_file_dir}/input.xml'
    msg = upload_file_to_github(tmpf, input_file_path)
    if 'error' in msg:
        logger.error(f"Error uploading input to GitHub: {msg}")
    
    # Read the user input classification prompt
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    with open(os.path.join(prompts_dir, 'user_input_classification.prompt'), 'r') as f:
        prompt = f.read()

    optional_text_input = ""
    if user_input_text:
        with open(os.path.join(prompts_dir, 'optional_text_input.prompt'), 'r') as f:
            optional_text_input = f.read()
            optional_text_input = optional_text_input.replace("{{USER_TEXT_INPUT}}", user_input_text)
            prompt = prompt.replace("{{OPTIONAL_TEXT_INPUT}}", optional_text_input)

    # Replace the placeholders with actual values
    content_input = [
        {"type": "text", "text": prompt}
    ]
    if image_input_dict:
        content_input.append(image_input_dict)
    logger.info(f"content_input: {content_input}")

    luleo_prompt = get_luleo_prompt()

    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": luleo_prompt},
            {"role": "user", "content": content_input}
        ]
    )

    raw_response = completion.choices[0].message.content
    logger.info("Raw API Response:")
    logger.info(raw_response)

    # Extract the learning, wisdom, love, and questions
    categories_match = re.search(r'<categories>(.*?)</categories>', raw_response, re.DOTALL)
    explanation_match = re.search(r'<explanation>(.*?)</explanation>', raw_response, re.DOTALL)
    
    assert categories_match, "Categories not found in the response"
    assert explanation_match, "Explanation not found in the response"

    categories = re.findall(r'<category>(.*?)</category>', categories_match.group(1))
    explanation = explanation_match.group(1).strip()

    input_xml_path = f'{gh_file_dir}/input.xml'
    
    d_update = {
        "final_prompt": content_input,
        "categories": categories,
        "explanation": explanation,
        "github_image_path" : gh_image_path,
    }
    db.collection("user_inputs").document(upload_id).update(d_update)
    return d_update

def get_latest_summary():
    # Get the latest summary from the summary collection
    docs = db.collection("summary").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).get()
    if len(docs) == 0:
        logger.error(f"No summary found")
        return None
    return docs[0].to_dict()

