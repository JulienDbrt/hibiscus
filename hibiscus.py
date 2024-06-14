import streamlit as st
from dotenv import load_dotenv
import pandas as pd
import json
import os
import dropbox

# Load environment variables from .env file
load_dotenv()

# Initialize Dropbox client
DROPBOX_TOKEN = os.getenv('DROPBOX_TOKEN')
if not DROPBOX_TOKEN:
    st.error("Dropbox access token is not set. Please check your .env file.")
dbx = dropbox.Dropbox(DROPBOX_TOKEN)

# Function to load the selected file from Dropbox
def load_data(file_option):
    try:
        _, res = dbx.files_download(f'/{file_option}')
        data = pd.read_csv(res.content)
        return data
    except dropbox.exceptions.AuthError as e:
        st.error(f"Dropbox authentication error: {e}")
    except Exception as e:
        st.error(f"Error loading file from Dropbox: {e}")

# Function to save the responses to Dropbox
def save_responses(user, responses):
    responses_df = pd.DataFrame(responses, columns=['Id', 'Response', 'User'])
    file_path = f'/{user}_responses.csv'
    try:
        dbx.files_upload(responses_df.to_csv(index=False).encode(), file_path, mode=dropbox.files.WriteMode.overwrite)
    except Exception as e:
        st.error(f"Error saving responses to Dropbox: {e}")

# Function to save the application state to Dropbox
def save_state(user):
    state = {
        'row_index': st.session_state.row_index,
        'responses': st.session_state.responses
    }
    file_path = f'/{user}_state.json'
    try:
        dbx.files_upload(json.dumps(state).encode(), file_path, mode=dropbox.files.WriteMode.overwrite)
    except Exception as e:
        st.error(f"Error saving state to Dropbox: {e}")

# Function to load the application state from Dropbox
def load_state(user):
    file_path = f'/{user}_state.json'
    try:
        _, res = dbx.files_download(file_path)
        state = json.loads(res.content)
        st.session_state.row_index = state['row_index']
        st.session_state.responses = state['responses']
    except dropbox.exceptions.ApiError:
        st.session_state.row_index = 0
        st.session_state.responses = []
    except Exception as e:
        st.error(f"Error loading state from Dropbox: {e}")

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
