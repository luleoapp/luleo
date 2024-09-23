import os 
from utils.db_init import db
from openai import OpenAI
from utils.logger_config import logger
from firebase_admin import firestore
import re


def compute_love_summary(limit=10):
    # Path to the prompts directory
    prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    
    # Read the Luleo system prompt
    with open(os.path.join(prompts_dir, 'luleo.prompt'), 'r') as f:
        luleo_prompt = f.read()
    
    # Read the summarize wisdom prompt
    with open(os.path.join(prompts_dir, 'summarize_love.prompt'), 'r') as f:
        summarize_love_prompt = f.read()

    # Query the most recent wisdom entries
    love_query = db.collection('love_understanding').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
    love_docs = love_query.get()

    # Collate the wisdom entries into a paragraph
    love_paragraph = "\n".join([doc.to_dict()['content'] for doc in love_docs])

    # Prepare the prompt for ChatGPT
    filled_prompt = summarize_love_prompt.replace('{{LOVE_PERSPECTIVES}}', love_paragraph)
    client = OpenAI()


    try:
        logger.info("Generating love summary")
        logger.info(f"\n\nFilled prompt: {filled_prompt}\n\n")

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
        love_summary_match = re.search(r'<love_summary>(.*?)</love_summary>', raw_response, re.DOTALL)

        return { "summary": love_summary_match.group(1).strip() }

    except Exception as e:
        print(f"Error generating love summary: {e}")
        return None

