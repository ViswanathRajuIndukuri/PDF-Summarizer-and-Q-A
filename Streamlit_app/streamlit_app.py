import streamlit as st
import requests
from streamlit_chat import message as chat_message

# Set the FastAPI backend URL
API_URL = "http://localhost:8000"

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'token' not in st.session_state:
    st.session_state.token = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'page' not in st.session_state:
    st.session_state.page = "signin"

def register():
    st.title("Sign Up")
    email = st.text_input("Email")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    password_confirm = st.text_input("Confirm Password", type="password")

    # Define callback functions
    def handle_register():
        if not email or not username or not password or not password_confirm:
            st.warning("Please fill in all fields")
        elif password != password_confirm:
            st.warning("Passwords do not match")
        else:
            response = requests.post(
                f"{API_URL}/register",
                json={
                    "email": email,
                    "username": username,
                    "password": password
                }
            )
            if response.status_code == 200:
                st.success("Registration successful! Please sign in.")
                st.session_state.page = "signin"
            else:
                error_detail = response.json().get('detail', 'Unknown error')
                st.error(f"Registration failed: {error_detail}")

    def go_back():
        st.session_state.page = "signin"

    col1, col2 = st.columns(2)
    with col1:
        st.button("Register", on_click=handle_register)
    with col2:
        st.button("Back", on_click=go_back)

def login():
    st.title("Sign In")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    # Define callback functions
    def handle_login():
        if not username or not password:
            st.warning("Please enter both username and password")
        else:
            response = requests.post(
                f"{API_URL}/login",
                data={
                    "username": username,
                    "password": password
                }
            )
            if response.status_code == 200:
                token = response.json().get("access_token")
                st.session_state.token = token
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.page = "welcome"
                st.success("Logged in successfully!")
            else:
                error_detail = response.json().get('detail', 'Unknown error')
                st.error(f"Login failed: {error_detail}")

    def go_to_signup():
        st.session_state.page = "signup"

    st.button("Sign In", on_click=handle_login)
    st.write("Don't have an account?")
    st.button("Sign Up", on_click=go_to_signup)

def welcome():
    st.title(f"Welcome, {st.session_state.username}!")
    st.write("You have successfully logged in.")

    # Initialize chat history
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Initialize input text
    if 'input_text' not in st.session_state:
        st.session_state.input_text = ''

    def handle_logout():
        st.session_state.logged_in = False
        st.session_state.token = None
        st.session_state.username = None
        st.session_state.page = "signin"
        st.success("You have been logged out.")

    # Log Out Button
    st.button("Log Out", on_click=handle_logout)

    st.write("---")  # Separator

    # Chat Interface
    st.subheader("Chat with Assistant")

    # Display chat history
    for i, chat in enumerate(st.session_state.chat_history):
        if chat['role'] == 'user':
            chat_message(chat['content'], is_user=True, key=f"user_{i}")
        else:
            chat_message(chat['content'], key=f"assistant_{i}")

    # Function to handle sending messages
    def send_message():
        user_input = st.session_state.input_text
        if user_input.strip() != '':
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            # Send the message to the backend
            headers = {
                "Authorization": f"Bearer {st.session_state.token}",
                "Content-Type": "application/json"
            }
            response = requests.post(
                f"{API_URL}/chat",
                headers=headers,
                json={"message": user_input}
            )

            if response.status_code == 200:
                assistant_reply = response.json().get("reply")
                # Add assistant's reply to chat history
                st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})
            else:
                error_detail = response.json().get('detail', 'Unknown error')
                st.error(f"Error: {error_detail}")

            # Clear the input text
            st.session_state.input_text = ''

    # Create the input box with on_change callback
    st.text_input("You:", key='input_text', on_change=send_message)


def main():
    if st.session_state.page == "signin":
        login()
    elif st.session_state.page == "signup":
        register()
    elif st.session_state.page == "welcome":
        if st.session_state.logged_in:
            welcome()
        else:
            st.session_state.page = "signin"
            login()

if __name__ == "__main__":
    main()
