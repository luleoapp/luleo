import os 
import tempfile
from utils.llm_utils import call_and_log_llm
from utils.file_processing import download_to_local_path, process_text_pdf
from utils.db_init import db
from utils.logger_config import system_logger
from firebase_admin import firestore
from utils.string_utils import get_user_input_document_path
from utils.github_utils import full_github_resource_path, upload_file_to_github
import os, json

def get_collection_path_to_category():
    return {
        'wisdom' : 'wisdom_inputs',
        'love' : 'love_inputs',
        'ai' : 'ai_inputs',
        'divine' : 'divine_inputs',
        'app' : 'app_inputs',
        'questions' : 'questions_inputs',
        'art' : 'art_inputs',
        'idea' : 'ideas_inputs',
        'feedback' : 'feedback_inputs',
        'miscellaneous' : 'miscellaneous_inputs',
        'spam' : 'spam_inputs',
    }

def process_user_upload(upload_id):
    doc = db.collection("user_inputs").document(upload_id).get()
    if not doc.exists:
        system_logger.error(f"ERROR : User input document {upload_id} does not exist")
        return None
    data = doc.to_dict()
    if not data.get("human"):
        system_logger.info(f"ERROR : User input {upload_id} is not human, skipping classification")
        return
    
    user_identity_str = data.get("user_identity_str")
    user_input_text = data.get("user_input_text","")
    user_file_url = data.get("file_url")
    user_input_image_path = None
    #check if file is pdf or image
    if user_file_url:
        if not user_file_url.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.pdf')):
            system_logger.error(f"ERROR : File input for {upload_id} is not an image or pdf, skipping file processing")  
        elif user_file_url.endswith('.pdf'):
            #get text from pdf
            text = process_text_pdf(user_file_url)
            if len(text) > 10000:
                user_input_text += "Attached pdf text:\n" + text[:10000]
            else:
                user_input_text += "Attached pdf text:\n" + text     
        else:
            #make sure it's an image file
        # Download the image from Firebase storage to a local file
            local_image_path = download_to_local_path(user_file_url)
            system_logger.info(f"Image downloaded successfully to {local_image_path}")
            user_input_image_path = local_image_path
    return classify_user_input(upload_id, user_identity_str, user_input_text, user_input_image_path)


def classify_user_input(upload_id, user_identity_str, user_input_text=None, user_input_image_path=None):
    #if both are none, return None
    if user_input_text is None and user_input_image_path is None:
        system_logger.error("No user input provided")
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
            system_logger.error(f"Error uploading image to GitHub: {msg}")
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
        system_logger.error(f"Error uploading input to GitHub: {msg}")
    
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
    system_logger.info(f"content_input: {content_input}")

    luleo_prompt = get_luleo_prompt()

    
    try:
        response_json = call_and_log_llm(system_prompt=luleo_prompt, user_prompt=content_input, model="gpt-4o")
        input_summary = response_json.get("input_summary")
        explanation = response_json.get("explanation")
        categories = response_json.get("categories")
    except json.JSONDecodeError as e:
        system_logger.error(f"Error decoding JSON: {e}")
        return
   
    d_update = {
        "final_prompt": content_input,
        "categories": categories,
        "explanation": explanation,
        "input_summary": input_summary,
        "github_image_path" : gh_image_path,
    }
    db.collection("user_inputs").document(upload_id).update(d_update)
    all_analysis_json = {}
    for category in categories:    
        analysis_json = get_analysis_from_category(upload_id,category, {
            "user_input_id" : upload_id,
            "user_identity" : user_identity_str,
            "user_input_text" : user_input_text,
            "user_input_image_path" : user_input_image_path,
            "github_image_path" : gh_image_path,
            "input_summary" : input_summary,
        })
        if analysis_json:
            all_analysis_json[f'{category}_analysis'] = analysis_json
    
    if all_analysis_json:
        all_analysis_json["processed_for_qualia"] = False
        db.collection("user_inputs").document(upload_id).update(all_analysis_json)
    
def analyze_input_for_category(upload_id):
    #standalone function to analyze the input for all categories
    doc = db.collection("user_inputs").document(upload_id).get()
    if not doc.exists:
        system_logger.error(f"ERROR : User input document {upload_id} does not exist")
        return None
    d_input = doc.to_dict()
    all_analysis_json = {}
    for category in d_input["categories"]:
        analysis_json = get_analysis_from_category(category, d_input)
        if analysis_json:
            all_analysis_json[f'{category}_analysis'] = analysis_json
    
    if all_analysis_json:
        if "processed_for_qualia" not in d_input:
            d_input["processed_for_qualia"] = False
        db.collection("user_inputs").document(upload_id).update(all_analysis_json)


def get_analysis_from_category(category,d_input):
    # get the analysis for the category
    # store the analysis in the category collection
    # update the input document with the analysis
    luleo_prompt = get_luleo_prompt()
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    analysis_prompt_file = os.path.join(prompts_dir, 'input_analyses', f'{category}.prompt')
    
    if not os.path.exists(analysis_prompt_file):
        system_logger.error(f"Analysis prompt file {analysis_prompt_file} does not exist")
        return None
    else:        
        with open(analysis_prompt_file, 'r') as f:
            analysis_prompt = f.read()
        input_str = f"{category.upper()}_INPUT"
        analysis_prompt = analysis_prompt.replace("{{"+input_str+"}}", d_input["input_summary"])
        system_logger.info(f"analysis_prompt: {analysis_prompt}")
    
    assert analysis_prompt, "Analysis prompt not found"

    try:
        analysis_json = call_and_log_llm(system_prompt=luleo_prompt, user_prompt=analysis_prompt, model="gpt-4o-mini")
        d_input.update(analysis_json)
        return analysis_json
    except Exception as e:
        system_logger.error(f"Error querying OpenAI API: {e}")
        return None

def get_latest_summary():
    # Get the latest summary from the summary collection
    docs = db.collection("summary").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).get()
    if len(docs) == 0:
        system_logger.error(f"No summary found")
        return None
    return docs[0].to_dict()

def get_luleo_prompt():
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    # Read the Luleo system prompt
    with open(os.path.join(prompts_dir, 'luleo.prompt'), 'r') as f:
        base_prompt = f.read()  
    #add summary
    summary = get_latest_summary()
    prompt = base_prompt.replace("{{WISDOM_SUMMARY}}", summary['wisdom_summary']).replace("{{LOVE_SUMMARY}}", summary['love_summary'])
    return prompt
