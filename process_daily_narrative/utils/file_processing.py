import io
from urllib.parse import urlparse
from PyPDF2 import PdfFileReader
import os
from github import Github, GithubException
import tempfile

import requests

def process_text_pdf(content, file_name):
    try:
        if file_name.endswith('.pdf'):
            reader = PdfFileReader(io.BytesIO(content))
            full_text = ""
            for page in range(reader.getNumPages()):
                full_text += reader.getPage(page).extract_text()
        else:
            full_text = content.decode('utf-8')
        return full_text,
    except Exception as e:
        print(f'Error processing text/PDF file {file_name}: {e}')
        return None

def download_to_local_path(url):
    try:
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as temp_file:
            response = requests.get(url)
            response.raise_for_status()
            temp_file.write(response.content)
            return temp_file.name
    except Exception as e:
        print(f"Error downloading file: {e}")
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