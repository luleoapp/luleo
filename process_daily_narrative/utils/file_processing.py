import io
from pydub import AudioSegment
from PyPDF2 import PdfFileReader
from PIL import Image
from utils.openai_api import call_openai_api, call_openai_image_api
from utils.pdf_generator import save_as_pdf
import json
import os
from github import Github, GithubException
from datetime import datetime


def process_audio_video(content, file_name):
    # Convert the content to an AudioSegment object

    # Throw an unimplemented error
    raise NotImplementedError("Processing audio/video files is not yet implemented")

def process_text_pdf(content, file_name):
    try:
        if file_name.endswith('.pdf'):
            reader = PdfFileReader(io.BytesIO(content))
            full_text = ""
            for page in range(reader.getNumPages()):
                full_text += reader.getPage(page).extract_text()
        else:
            full_text = content.decode('utf-8')
        summary = call_openai_api(full_text, 'summary')
        return full_text, summary
    except Exception as e:
        print(f'Error processing text/PDF file {file_name}: {e}')
        return None, None

def process_image(content, file_name):
    d_vals = call_openai_image_api(content)
    if d_vals["is_inappropriate"]:
        return None 
    return d_vals["description"]

def process_file_content(file_name, content):
    mime_type = file_name.split('.')[-1]
    try: 
        if mime_type in ['mp4', 'mp3', 'wav']:
            transcription, summary = process_audio_video(content, file_name)
            return None
        elif mime_type in ['txt', 'pdf']:
            full_text, summary = process_text_pdf(content, file_name)
            text_content = full_text if len(full_text.split()) < 500 else summary
            pdf_file = save_as_pdf(file_name, text_content)
            return pdf_file
        elif mime_type in ['jpg', 'jpeg', 'png']:
            description = process_image(content, file_name)
            pdf_file = save_as_pdf(file_name, content)
            return pdf_file 
    except Exception as e:
        print(f'Error processing file {file_name}: {e}')
    print(f'ERROR - DID NOT GET PDF')
    return None


# Create GitHub folder with nested subfolders
def create_daily_folder():
    github_token = os.environ.get('GITHUB_TOKEN')
    repo_name = os.environ.get('GITHUB_REPO_NAME')

    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is not set")
    if not repo_name:
        raise ValueError("GITHUB_REPO_NAME environment variable is not set")

    print(f"Attempting to access repository: {repo_name}")
    
    g = Github(github_token)
    
    try:
        # First, try to get the authenticated user
        user = g.get_user()
        print(f"Authenticated as user: {user.login}")
        
        # Then, try to get the repository
        repo = user.get_repo(repo_name.split('/')[-1])  # Use only the repo name, not the full path
        print(f"Successfully accessed repository: {repo.full_name}")
        
        # Your existing code to create the daily folder goes here
        
    except GithubException as e:
        if e.status == 404:
            print(f"Repository not found: {repo_name}")
            print("Please check if the repository name is correct and if you have access to it.")
        elif e.status == 401:
            print("Authentication failed. Please check your GitHub token.")
        else:
            print(f"GitHub API error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise