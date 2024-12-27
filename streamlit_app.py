import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as gpt
from functions import *

# Load environment variables from .env file for secure API key storage
load_dotenv()

# Configure Streamlit page settings for better user interface
st.set_page_config(
    page_title="Linux Lab Generator",
    page_icon=":robot_face:",  # Favicon emoji for browser tab
    layout="wide",  # Uses full screen width for better content display
)

# Retrieve API key from environment variables for security
API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize Google's Gemini-Pro AI model with API key
gpt.configure(api_key=API_KEY)
model = gpt.GenerativeModel('gemini-pro')

# Initialize or retrieve existing chat session from Streamlit's session state
initialize_chat_session(model)

# Main application title display
st.title("🤖 Linux Lab Generator")

# Sidebar implementation for session management
with st.sidebar:
    st.title("Lab Sessions")
    manage_sessions(model)

# Initialize display history for chat messages if not present
initialize_display_history()

# Create form for lab generation
create_lab_generation_form()

# Display chat history
display_chat_history()

# Chat interface for follow-up questions
handle_user_input()
