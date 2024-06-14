import streamlit as st
import pandas as pd
import json
import os

# Function to load the selected file
def load_data(file_option):
    if file_option == 'quanti.csv':
        return pd.read_csv('quanti.csv')
    elif file_option == 'quali.csv':
        return pd.read_csv('quali.csv')

# Function to save the responses
def save_responses(user, responses):
    responses_df = pd.DataFrame(responses, columns=['Id', 'Response', 'User'])
    responses_df.to_csv(f'{user}_responses.csv', index=False)

# Function to save the application state
def save_state(user):
    state = {
        'row_index': st.session_state.row_index,
        'responses': st.session_state.responses
    }
    with open(f'{user}_state.json', 'w') as f:
        json.dump(state, f)

# Function to load the application state
def load_state(user):
    if os.path.exists(f'{user}_state.json'):
        with open(f'{user}_state.json', 'r') as f:
            state = json.load(f)
            st.session_state.row_index = state['row_index']
            st.session_state.responses = state['responses']
    else:
        st.session_state.row_index = 0
        st.session_state.responses = []

# Sidebar with logo, file selection, and user selection
st.sidebar.image('logo_Erwin.png', use_column_width=True)  # Update with your logo path
file_option = st.sidebar.radio("Choose the file", ('quanti.csv', 'quali.csv'))
user_option = st.sidebar.selectbox("Select the user", ('Alberto', 'Julien', 'Emilie'))

# Load the selected file
data = load_data(file_option)

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
                st.experimental_rerun()
        with col2:
            if st.button('Pass', on_click=handle_response, args=('Pass',)):
                st.experimental_rerun()

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
