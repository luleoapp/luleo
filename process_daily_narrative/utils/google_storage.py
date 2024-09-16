from google.cloud import storage
from datetime import datetime
import os


def upload_file_to_gcs(bucket_name, source_file_name, destination_folder_name, today):
    # initialize a client
    storage_client = storage.Client()

    # get the bucket
    bucket = storage_client.bucket(bucket_name)

    # create a folder with today's date if it doesn't exist
   
    folder_path = f"{destination_folder_name}/{today}/"

    # create a blob for the file
    blob = bucket.blob(f"{folder_path}{os.path.basename(source_file_name)}")

    # upload the file
    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {folder_path}.")
