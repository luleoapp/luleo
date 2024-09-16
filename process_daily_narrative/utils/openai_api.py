import base64
import requests
import openai
import os 
import json 
from pathlib import Path
import anthropic 

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
PERPLEXITY_API_KEY = os.environ["PERPLEXITY_API_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]

def get_article_summary(content):
    
    prompt = f"""
    Please provide a concise summary of the following article. \
    The summary should be about 200 words long and capture the main points and key ideas:\
    Do not prepend ANY text like 'Here's a summary of...'\
    {content}

    Summary:
    """
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    message = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.choices[0].message.content


def call_openai_api(content, task):
    try:
        if task == 'transcription':
            response = openai.Audio.transcribe(model="whisper-1", file=content)
            return response['text']
        elif task == 'summary':
            return get_article_summary(content)
       
    except Exception as e:
        print(f'Error with OpenAI API: {e}')
        return None

def get_perplexity_client():
    return openai.OpenAI(api_key=PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")

def get_openrouter_client():
    return openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )

def encode_image(image_content):
    return base64.b64encode(image_content).decode('utf-8')

def call_openai_image_api(image_content):
    base64_image = encode_image(image_content)
    client = openai.OpenAI()
    response = client.chat.completions.create(
            model="gpt-4o",
            response_format= { "type":"json_object" },
            messages=[
                {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image, and flag it inappropriately sexual or violent. Return a json with fields <description> and <is_inappropriate>."},
                    {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                    },
                    },
                ],
                }
            ],
            max_tokens=300,
            )
    return json.loads(response.choices[0].message.content)


def get_prompt(prompt_name, directory="prompts"):
    prompt_file = directory +"/"+ f"{prompt_name}.prompt"
    
    with open(prompt_file, 'r') as file:
        return file.read()

'''
def get_daily_news():
    prompt = get_prompt("get_daily_news")
    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
            "role": "user",
            "content":  prompt},
            
        ],
        response_format={ "type": "json_object" }
    )

    return response 
'''

