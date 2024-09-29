from utils import llm_utils
from utils.qualia import generate_image_from_prompt
from utils.drive import upload_file_to_github
from utils.db_init import db
import os
import re
import logging
from datetime import datetime
from openai import OpenAI  # Assuming there's a module handling OpenAI interactions
from utils.logger_config import system_logger
from firebase_admin import firestore



def generate_wisdom_image(date_str):
    wisdom_doc = get_wisdom_doc(date_str)
    if not wisdom_doc:
        system_logger.error(f"No wisdom document found for {date_str}")
        return False
    return get_image_for_wisdom(date_str, wisdom_doc)


def get_wisdom_doc(date_str):
    doc = db.collection("daily_wisdom").document(date_str).get()
    if not doc.exists:
        system_logger.error(f"No wisdom document found for {date_str}")
        return None
    return doc.to_dict()


def get_image_for_wisdom(date_str, wisdom_doc):
    """
    Generates an image based on a wisdom quote, uploads it to GitHub, and updates the Firestore document
    with the image prompt and image URL.

    Args:
        wisdom_doc (dict): A dictionary representing a wisdom document from Firestore. Expected to contain:
                           - 'content': The wisdom quote.
                           - 'timestamp': The timestamp of the wisdom entry.
                           - 'image_prompt' (optional): Existing image prompt.
                           - 'image_url' (optional): Existing image URL.

    Returns:
        bool: True if the image was successfully generated and stored, False otherwise.
    """
    if not wisdom_doc or 'content' not in wisdom_doc:
        system_logger.error("Invalid wisdom document. 'content' field is missing.")
        return False

    wisdom_quote = wisdom_doc['content']
    gh_date_str = date_str[:4]+'-'+date_str[4:6]+'-'+date_str[6:]
    
    system_logger.info(f"Generating image for wisdom entry dated {date_str}: {wisdom_quote}")

    # Path to the prompts directory
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    from utils.luleo import get_luleo_prompt
    luleo_prompt = get_luleo_prompt()

    # Read the image prompt template
    with open(os.path.join(prompts_dir, 'wisdom_image_prompt.prompt'), 'r') as f:
        image_prompt_template = f.read()

    # Fill the prompt template with the wisdom quote
    filled_prompt = image_prompt_template.replace('{{WISDOM_QUOTE}}', wisdom_quote)
    system_logger.info(f"Filled Image Prompt: {filled_prompt}")

  
    # Initialize OpenAI client
    client = OpenAI()

    try:
        response_json = llm_utils.call_and_log_llm(filled_prompt, luleo_prompt, "gpt-4o-mini")
        image_prompt = response_json['image_prompt']
    except Exception as e:
        system_logger.error(f"Error generating image prompt with OpenAI: {e}")
        return False

    # Generate the image using the extracted image prompt
    try:
        image = generate_image_from_prompt(image_prompt)
        if not image:
            system_logger.error("Image generation failed.")
            return False
        system_logger.info("Image successfully generated.")
    except Exception as e:
        system_logger.error(f"Error generating image from prompt: {e}")
        return False

    # Define the image filename and path
    image_filename = f"wisdom_{date_str}.png"
    local_image_path = os.path.join(os.path.dirname(__file__), '..', 'outputs/images', image_filename)

    # Save the image locally
    try:
        with open(local_image_path, 'wb') as img_file:
            img_file.write(image)
        system_logger.info(f"Image saved locally at {local_image_path}")
    except Exception as e:
        system_logger.error(f"Error saving image locally: {e}")
        return False

    upload_path = f'daily_data/{gh_date_str}/outputs/wisdom_images/{image_filename}'
    # Upload the image to GitHub
    try:
        github_image_url = upload_file_to_github(local_image_path, upload_path)
        if not github_image_url:
            system_logger.error("Failed to upload image to GitHub.")
            return False
        system_logger.info(f"Image uploaded to GitHub at {github_image_url}")
    except Exception as e:
        system_logger.error(f"Error uploading image to GitHub: {e}")
        return False

    # Update the Firestore wisdom document with the image prompt and image URL
    try:
        wisdom_doc_ref = db.collection('daily_wisdom').document(date_str)
        wisdom_doc_ref.update({
            'image_prompt': image_prompt,
            'image_url': upload_path
        })
        system_logger.info(f"Firestore document updated with image details for {date_str}")
    except Exception as e:
        system_logger.error(f"Error updating Firestore document: {e}")
        return False
    finally:
        # Optionally, remove the local image file after upload
        try:
            os.remove(local_image_path)
            system_logger.info(f"Local image file {local_image_path} removed.")
        except Exception as e:
            system_logger.warning(f"Could not remove local image file: {e}")

    return True



def compute_wisdom_summary(limit=10):
    system_logger.info(f"Starting compute_wisdom_summary with limit {limit}")
    
    # Path to the prompts directory
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    system_logger.debug(f"Prompts directory: {prompts_dir}")
    
    # Read the Luleo system prompt
    from utils.luleo import get_luleo_prompt
    luleo_prompt = get_luleo_prompt()
    system_logger.debug("Luleo prompt retrieved")
    
    # Read the summarize wisdom prompt
    try:
        with open(os.path.join(prompts_dir, 'summarize_wisdom.prompt'), 'r') as f:
            summarize_wisdom_prompt = f.read()
        system_logger.debug("Summarize wisdom prompt read successfully")
    except Exception as e:
        system_logger.error(f"Error reading summarize wisdom prompt: {e}")
        return None

    # Query the most recent wisdom entries
    wisdom_query = db.collection('daily_wisdom').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
    wisdom_docs = wisdom_query.get()
    system_logger.info(f"Retrieved {len(wisdom_docs)} wisdom entries")

    # Collate the wisdom entries into a paragraph
    wisdom_paragraph = "\n".join([doc.to_dict()['content'] for doc in wisdom_docs])
    system_logger.debug("Wisdom entries collated into paragraph")

    # Prepare the prompt for ChatGPT
    filled_prompt = summarize_wisdom_prompt.replace('{{WISDOM_PARAGRAPHS}}', wisdom_paragraph)
    system_logger.debug("Prompt prepared for ChatGPT")
    
    try:
        response_json = llm_utils.call_and_log_llm(filled_prompt, luleo_prompt, "gpt-4o-mini")
        wisdom_summary = response_json['wisdom_summary']
        system_logger.info("Wisdom summary generated successfully")
        return { "summary": wisdom_summary }

    except Exception as e:
        system_logger.error(f"Error generating wisdom summary: {e}")
        return None

