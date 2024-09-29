import io
from urllib.parse import urlparse
from PyPDF2 import PdfFileReader
import os
from github import Github, GithubException
import tempfile
from datetime import datetime
import base64

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
    
