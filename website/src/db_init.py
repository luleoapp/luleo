import os
from firebase_admin import firestore, initialize_app, credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
import pytz
from dotenv import load_dotenv

load_dotenv()

PROJECT_TIMEZONE = pytz.timezone('America/New_York')

def get_cred_dict():
    return {   
        "type": "service_account",
        "project_id": os.environ.get("GCP_PROJECT_ID"),
        "private_key_id": os.environ.get("GCP_PRIVATE_KEY_ID"),
        "private_key": os.environ.get("GCP_PRIVATE_KEY").replace('\\n', '\n'),
        "client_email": os.environ.get("GCP_CLIENT_EMAIL"),
        "client_id": os.environ.get("GCP_CLIENT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.environ.get("GCP_CLIENT_X509_CERT_URL")
    }

# Function to authenticate based on the environment
def get_credentials():
# Instead, use environment variables
    credentials_info = get_cred_dict()

    return service_account.Credentials.from_service_account_info(credentials_info)

# Authenticate and initialize the Drive API client
service_account_credentials = get_credentials()
drive_service = build('drive', 'v3', credentials=service_account_credentials)


firebase_credentials = credentials.Certificate(get_cred_dict())
firebase_app = initialize_app(firebase_credentials, name=os.environ["FIREBASE_APP_NAME"])

db = firestore.client(app=firebase_app)
print(f"Connected to Firestore database: {os.environ['FIRESTORE_DB_NAME']}")
print("TODO : Bug - should connect to the right database, but connects to default")


def github_path(image_path):
    return "https://raw.githubusercontent.com/luleoapp/luleo/main/"+image_path
