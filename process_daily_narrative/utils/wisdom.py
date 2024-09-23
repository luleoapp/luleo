from utils.qualia import generate_image_from_prompt
from utils.drive import upload_file_to_github
from utils.db_init import db
import os
import re
import logging
from datetime import datetime
from openai import OpenAI  # Assuming there's a module handling OpenAI interactions
from utils.logger_config import logger
from firebase_admin import firestore



def generate_wisdom_image(date_str):
    wisdom_doc = get_wisdom_doc(date_str)
    if not wisdom_doc:
        logger.error(f"No wisdom document found for {date_str}")
        return False
    return get_image_for_wisdom(date_str, wisdom_doc)


def get_wisdom_doc(date_str):
    doc = db.collection("daily_wisdom").document(date_str).get()
    if not doc.exists:
        logger.error(f"No wisdom document found for {date_str}")
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
        logger.error("Invalid wisdom document. 'content' field is missing.")
        return False

    wisdom_quote = wisdom_doc['content']
    gh_date_str = date_str[:4]+'-'+date_str[4:6]+'-'+date_str[6:]
    
    logger.info(f"Generating image for wisdom entry dated {date_str}: {wisdom_quote}")

    # Path to the prompts directory
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    from utils.luleo import get_luleo_prompt
    luleo_prompt = get_luleo_prompt()

    # Read the image prompt template
    with open(os.path.join(prompts_dir, 'wisdom_image_prompt.prompt'), 'r') as f:
        image_prompt_template = f.read()

    # Fill the prompt template with the wisdom quote
    filled_prompt = image_prompt_template.replace('{{WISDOM_QUOTE}}', wisdom_quote)
    logger.info(f"Filled Image Prompt: {filled_prompt}")

    # Initialize OpenAI client
    client = OpenAI()

    try:
        # Generate the image prompt using OpenAI
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": luleo_prompt},
                {"role": "user", "content": filled_prompt}
            ]
        )

        raw_response = completion.choices[0].message.content
        logger.info("Raw GPT Response for Image Prompt:")
        logger.info(raw_response)

        # Extract the image prompt from the GPT response
        image_prompt_match = re.search(r'<image_prompt>(.*?)</image_prompt>', raw_response, re.DOTALL)
        if not image_prompt_match:
            logger.error("Image prompt not found in the GPT response.")
            return False

        image_prompt = image_prompt_match.group(1).strip()
        logger.info(f"Extracted Image Prompt: {image_prompt}")

    except Exception as e:
        logger.error(f"Error generating image prompt with OpenAI: {e}")
        return False

    # Generate the image using the extracted image prompt
    try:
        image = generate_image_from_prompt(image_prompt)
        if not image:
            logger.error("Image generation failed.")
            return False
        logger.info("Image successfully generated.")
    except Exception as e:
        logger.error(f"Error generating image from prompt: {e}")
        return False

    # Define the image filename and path
    image_filename = f"wisdom_{date_str}.png"
    local_image_path = os.path.join(os.path.dirname(__file__), '..', 'outputs/images', image_filename)

    # Save the image locally
    try:
        with open(local_image_path, 'wb') as img_file:
            img_file.write(image)
        logger.info(f"Image saved locally at {local_image_path}")
    except Exception as e:
        logger.error(f"Error saving image locally: {e}")
        return False

    upload_path = f'daily_data/{gh_date_str}/outputs/wisdom_images/{image_filename}'
    # Upload the image to GitHub
    try:
        github_image_url = upload_file_to_github(local_image_path, upload_path)
        if not github_image_url:
            logger.error("Failed to upload image to GitHub.")
            return False
        logger.info(f"Image uploaded to GitHub at {github_image_url}")
    except Exception as e:
        logger.error(f"Error uploading image to GitHub: {e}")
        return False

    # Update the Firestore wisdom document with the image prompt and image URL
    try:
        wisdom_doc_ref = db.collection('daily_wisdom').document(date_str)
        wisdom_doc_ref.update({
            'image_prompt': image_prompt,
            'image_url': upload_path
        })
        logger.info(f"Firestore document updated with image details for {date_str}")
    except Exception as e:
        logger.error(f"Error updating Firestore document: {e}")
        return False
    finally:
        # Optionally, remove the local image file after upload
        try:
            os.remove(local_image_path)
            logger.info(f"Local image file {local_image_path} removed.")
        except Exception as e:
            logger.warning(f"Could not remove local image file: {e}")

    return True



def compute_wisdom_summary(limit=10):
    # Path to the prompts directory
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    
    # Read the Luleo system prompt
    from utils.luleo import get_luleo_prompt
    luleo_prompt = get_luleo_prompt()
    
    # Read the summarize wisdom prompt
    with open(os.path.join(prompts_dir, 'summarize_wisdom.prompt'), 'r') as f:
        summarize_wisdom_prompt = f.read()

    # Query the most recent wisdom entries
    wisdom_query = db.collection('daily_wisdom').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
    wisdom_docs = wisdom_query.get()

    # Collate the wisdom entries into a paragraph
    wisdom_paragraph = "\n".join([doc.to_dict()['content'] for doc in wisdom_docs])

    # Prepare the prompt for ChatGPT
    filled_prompt = summarize_wisdom_prompt.replace('{{WISDOM_PARAGRAPHS}}', wisdom_paragraph)
    client = OpenAI()

    try:
        # Generate the summary using OpenAI
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": luleo_prompt},
                {"role": "user", "content": filled_prompt}
            ]
        )
        # Extract the summary from the response
        raw_response = completion.choices[0].message.content
        logger.info("Raw GPT Response for Image Prompt:")
        logger.info(raw_response)

        # Extract the image prompt from the GPT response
        wisdom_summary_match = re.search(r'<wisdom_summary>(.*?)</wisdom_summary>', raw_response, re.DOTALL)

        return { "summary": wisdom_summary_match.group(1).strip() }

    except Exception as e:
        print(f"Error generating wisdom summary: {e}")
        return None

