import streamlit as st
import pandas as pd
import json
import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from io import BytesIO

# Authenticate and create the PyDrive client
def authenticate_drive():
    gauth = GoogleAuth()
    gauth.DEFAULT_SETTINGS['client_config_file'] = "credentials.json"
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
        file_list = drive.ListFile({'q': f"title='{file_name}'"}).GetList()
        if file_list:
            file = drive.CreateFile({'id': file_list[0]['id']})
        else:
            file = drive.CreateFile({'title': file_name})
        file.SetContentString(responses_df.to_csv(index=False))
        file.Upload()
    except Exception as e:
        st.error(f"Error saving responses to Google Drive: {e}")

# Function to save the application state to Google Drive
def save_state(user):
    state = {
        'row_index': st.session_state.row_index,
        'responses': st.session_state.responses
    }
    file_name = f'{user}_state.json'
    try:
        file_list = drive.ListFile({'q': f"title='{file_name}'"}).GetList()
        if file_list:
            file = drive.CreateFile({'id': file_list[0]['id']})
        else:
            file = drive.CreateFile({'title': file_name})
        file.SetContentString(json.dumps(state))
        file.Upload()
    except Exception as e:
        st.error(f"Error saving state to Google Drive: {e}")

# Function to load the application state from Google Drive
def load_state(user):
    file_name = f'{user}_state.json'
    try:
        file_list = drive.ListFile({'q': f"title='{file_name}'"}).GetList()
        if file_list:
            file_id = file_list[0]['id']
            file_content = drive.CreateFile({'id': file_id}).GetContentString()
            state = json.loads(file_content)
            st.session_state.row_index = state['row_index']
            st.session_state.responses = state['responses']
        else:
            st.session_state.row_index = 0
            st.session_state.responses = []
    except Exception as e:
        st.error(f"Error loading state from Google Drive: {e}")

# Sidebar with logo, file selection, and user selection
st.sidebar.image('logo_Erwin.png', use_column_width=True)  # Update with your logo path
file_option = st.sidebar.radio("Choose the file", ('quanti.csv', 'quali.csv'))
user_option = st.sidebar.selectbox("Select the user", ('Alberto', 'Julien', 'Emilie'))

# Load the selected file
data = load_data(file_option)

if data is not None:
    # Strip any leading/trailing whitespace from column names
    data.columns = data.columns.str.strip()

    # Check if 'Id.' column exists
    if 'Id.' not in data.columns:
        st.error("The column 'Id.' was not found in the file. Available columns are:")
        st.write(data.columns.tolist())
    else:
        # Main content
        st.title('Data Review Interface')

        # Function to handle response and save progress
        def handle_response(response):
            st.session_state.responses.append((data.iloc[st.session_state.row_index]['Id.'], response, user_option))
            st.session_state.row_index += 1
            save_responses(user_option, st.session_state.responses)
            save_state(user_option)

        # Initialize session state for keeping track of the row index and responses
        if 'last_user' not in st.session_state or st.session_state.last_user != user_option:
            load_state(user_option)
            st.session_state.last_user = user_option

        # Display the current row as columns
        if st.session_state.row_index < len(data):
            row = data.iloc[st.session_state.row_index]
            for col in row.index:
                st.write(f"**{col}**: {row[col]}")

            # Buttons for user to respond
            col1, col2 = st.columns(2)
            with col1:
                if st.button('Keep', on_click=handle_response, args=('Keep',)):
                    st.rerun()
            with col2:
                if st.button('Pass', on_click=handle_response, args=('Pass',)):
                    st.rerun()

            # Save responses when done
            if st.session_state.row_index >= len(data):
                st.write("All rows have been processed and responses have been saved.")
        else:
            st.write("All rows have been processed and responses have been saved.")

    # Option to download the responses file
    if st.session_state.responses:
        st.download_button(
            label="Download responses",
            data=pd.DataFrame(st.session_state.responses, columns=['Id', 'Response', 'User']).to_csv(index=False),
            file_name=f'{user_option}_responses.csv',
            mime='text/csv',
        )
