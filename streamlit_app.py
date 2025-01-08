import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as gpt
from functions import *
from authenticator import authenticator

# Load environment variables from .env file for secure API key storage
load_dotenv()
# Configure Streamlit page settings for better user interface
st.set_page_config(
    page_title="Linux Lab Generator",
    page_icon=":robot_face:",  # Favicon emoji for browser tab
    layout="wide",  # Uses full screen width for better content display
)

# Retrieve API key from environment variables for security
#API_KEY = os.getenv("GOOGLE_API_KEY")
API_KEY=st.secrets["gemini_api_key"]
# Initialize Google's Gemini-Pro AI model with API key
gpt.configure(api_key=API_KEY)
model = gpt.GenerativeModel('gemini-pro')

def main():
    authenticator(model)
    
    # Check if the user is logged in
    if 'username' not in st.session_state:
        st.warning("Please log in to access the Linux Lab Generator.")
        return  # Exit the main function if not logged in

    # Initialize or retrieve existing chat session from Streamlit's session state
    initialize_chat_session(model)

    # Header Section
    st.markdown("<h1 style='text-align: center; color: black;'>🤖 IITG Linux and Cybersecurity Lab Generator (2024-2025)</h1>", unsafe_allow_html=True)
    st.markdown("<hr style='height: 5px; border: none; background-color: #333; margin-bottom: 20px;'>", unsafe_allow_html=True)

    # Sidebar implementation for session management
    with st.sidebar:
        st.title("Lab Sessions")
        manage_sessions(model)

    # Initialize display history for chat messages if not present
    initialize_display_history()

    # Create form for lab generation
    create_lab_generation_form()

    # Display generated lab information if available
    display_generated_lab_info()

    # Display chat history
    display_chat_history()

    # Chat interface for follow-up questions
    handle_user_input()



if __name__ == "__main__":
    main()
