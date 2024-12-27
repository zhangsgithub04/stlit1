import streamlit as st
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import datetime


MONGODB_URI = "mongodb+srv://dbAdmin:admin1@cluster0.iwwoeb1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


load_dotenv()

def get_database():
    client = MongoClient(MONGODB_URI)
    return client['linux_lab_db']

def map_role(role):
    if role == "model":
        return "assistant"
    else:
        return role

def fetch_gemini_response(user_query):
    try:
        response = st.session_state.chat_session.send_message(user_query)
        return response.text
    except Exception as e:
        st.error(f"Error generating response: {e}")
        return "I apologize, but I encountered an error generating a response. Please try again."

def save_session(session_name, chat_history):
    """
    Saves the chat session to MongoDB with proper formatting.
    The chat_history parameter can be either:
    1. A list of Content objects (from Gemini's chat session)
    2. A list of dictionaries (from our display history)
    """
    db = get_database()
    sessions_collection = db['sessions']
    
    # Format the history based on its type
    formatted_history = []
    
    # Check if we're dealing with display_history (list of dicts) or chat session history (list of Content objects)
    if chat_history and isinstance(chat_history[0], dict):
        # If it's already in our display history format, use it directly
        formatted_history = chat_history
    else:
        # If it's from Gemini's chat session, we need to format it
        for message in chat_history:
            # Get the role
            role = message.role
            # Get the content
            content = message.parts[0].text
            
            formatted_history.append({
                "role": role,
                "content": content
            })
    
    try:
        sessions_collection.update_one(
            {"session_name": session_name},
            {
                "$set": {
                    "session_name": session_name,
                    "chat_history": formatted_history,
                    "last_modified": datetime.datetime.utcnow()
                }
            },
            upsert=True
        )
        return True
    except Exception as e:
        st.error(f"An error occurred while saving the session: {e}")
        return False

def load_session(session_name, model):
    db = get_database()
    sessions_collection = db['sessions']
    session = sessions_collection.find_one({"session_name": session_name})
    
    if not session:
        return model.start_chat(history=[]), []

    # Create a list of properly formatted messages for Gemini
    gemini_messages = []
    for message in session['chat_history']:
        # Format each message as Gemini expects
        if message['role'] == 'user':
            gemini_messages.append({
                'role': 'user',
                'parts': [{'text': message['content']}]
            })
        else:
            gemini_messages.append({
                'role': 'model',
                'parts': [{'text': message['content']}]
            })
    
    # Start a new chat with the formatted history
    chat = model.start_chat(history=gemini_messages)
    
    # Return both the chat object and the display history
    return chat, session['chat_history']

def get_saved_sessions():
    db = get_database()
    sessions_collection = db['sessions']
    sessions = sessions_collection.find({}, {"session_name": 1, "last_modified": 1}).sort("last_modified", -1) #sort history by last modified
    return [session['session_name'] for session in sessions]

def delete_session(session_name):
    db = get_database()
    sessions_collection = db['sessions']
    result = sessions_collection.delete_one({"session_name": session_name})
    return result.deleted_count > 0

def initialize_chat_session(model):
    if "chat_session" not in st.session_state:
        st.session_state.chat_session = model.start_chat(history=[])

def manage_sessions(model):
    if st.button("Start New Session"):
        st.session_state.chat_session = model.start_chat(history=[])
        st.session_state.display_history = []
        st.session_state.current_session = None
        st.session_state.lab_generated = False
        st.session_state.generated_lab = None
        if 'lab_query' in st.session_state:
            del st.session_state.lab_query
        st.rerun()

    view_tab, delete_tab = st.tabs(["View History", "Delete History"])
    saved_sessions = get_saved_sessions()

    with view_tab:
        st.subheader("History")
        for session in saved_sessions:
            if st.button(session, key=f"view_{session}"):
                new_chat, history = load_session(session, model)
                st.session_state.chat_session = new_chat
                st.session_state.display_history = history
                st.session_state.current_session = session
                st.rerun()

    with delete_tab:
        st.subheader("Select Sessions to Delete")
        for session in saved_sessions:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.text(session)
            with col2:
                if st.button("❌", key=f"delete_{session}"):
                    delete_session(session)
                    st.rerun()

def initialize_display_history():
    if "display_history" not in st.session_state:
        st.session_state.display_history = []

def create_lab_generation_form():
    with st.form(key='lab_generation_form'):
        st.subheader("Lab Configuration")
        linux_distros = ["Debian", "Arch", "Kali", "Ubuntu", "Fedora", "CentOS"]
        selected_distro = st.selectbox("Select a Linux Distribution", linux_distros)
        lab_query = st.text_input("Generate Lab Query")
        submit_button = st.form_submit_button("Generate Lab")

        if submit_button and lab_query:
            prompt = f"Please create a linux lab manual for {selected_distro} with respect to {lab_query} using detailed commands, options, and explanations step by step."
            lab_response = fetch_gemini_response(prompt)
            
            # Store in display history
            st.session_state.generated_lab = lab_response
            st.session_state.lab_generated = True
            st.session_state.display_history = [{"role": "model", "content": lab_response}]
            
            # Save the session using display history
            save_session(lab_query, st.session_state.display_history)
            st.session_state.current_session = lab_query
            
            st.rerun()

def display_chat_history():
    for msg in st.session_state.display_history:
        with st.chat_message(map_role(msg["role"])):
            st.markdown(msg["content"])

def handle_user_input():
    user_input = st.chat_input("Ask about the lab...")
    if user_input:
        # Display user message
        st.chat_message("user").markdown(user_input)
        
        try:
            # Use send_message to maintain conversation context
            response = st.session_state.chat_session.send_message(user_input)
            response_text = response.text
            
            # Display assistant response
            with st.chat_message("assistant"):
                st.markdown(response_text)
            
            # Update display history
            st.session_state.display_history.append({"role": "user", "content": user_input})
            st.session_state.display_history.append({"role": "model", "content": response_text})
            
            # Save the updated session
            if hasattr(st.session_state, 'current_session') and st.session_state.current_session:
                save_session(st.session_state.current_session, st.session_state.display_history)
                
        except Exception as e:
            st.error(f"Error processing your message: {e}")
