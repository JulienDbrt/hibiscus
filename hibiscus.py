import streamlit as st
import pandas as pd
import json
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from io import BytesIO
import tempfile

# Authenticate and create the PyDrive client
def authenticate_drive():
    gauth = GoogleAuth()
    # Use environment variable to store the credentials JSON
    creds_json = st.secrets.db_credentials.username
    if creds_json:
        with tempfile.NamedTemporaryFile(delete=False) as temp_creds:
            temp_creds.write(creds_json.encode())
            temp_creds.flush()
            gauth.LoadCredentialsFile(temp_creds.name)
            os.unlink(temp_creds.name)
    else:
        gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    return drive

drive = authenticate_drive()

# Function to load the selected file from Google Drive or local
def load_data(file_option):
    try:
        # Attempt to load from Google Drive
        file_list = drive.ListFile({'q': f"title='{file_option}'"}).GetList()
        if not file_list:
            st.warning(f"File not found in Google Drive, trying to load from local: {file_option}")
            if os.path.isfile(file_option):
                data = pd.read_csv(file_option)
                return data
            else:
                st.error(f"File {file_option} not found locally either.")
        else:
            file_id = file_list[0]['id']
            file_content = drive.CreateFile({'id': file_id}).GetContentString()
            data = pd.read_csv(BytesIO(file_content.encode()))
            return data
    except Exception as e:
        st.error(f"Unexpected error: {e}")

# Function to save the responses to Google Drive
def save_responses(user, responses):
    responses_df = pd.DataFrame(responses, columns=['Id', 'Response', 'User'])
    file_name = f'{user}_responses.csv'
    try:
        file_
