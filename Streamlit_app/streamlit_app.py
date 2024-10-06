import streamlit as st
import requests

# Set the FastAPI backend URL
API_URL = "http://localhost:8000"  # Replace with your actual backend URL if different

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
                st.session_state.page = "home"
                st.success("Logged in successfully!")
            else:
                error_detail = response.json().get('detail', 'Unknown error')
                st.error(f"Login failed: {error_detail}")

    def go_to_signup():
        st.session_state.page = "signup"

    st.button("Sign In", on_click=handle_login)
    st.write("Don't have an account?")
    st.button("Sign Up", on_click=go_to_signup)

def home():
    st.title("PDF Summarizer and Q&A")
    st.write("Select a PDF file and choose an action.")

    def handle_logout():
        st.session_state.logged_in = False
        st.session_state.token = None
        st.session_state.username = None
        st.session_state.page = "signin"
        st.success("You have been logged out.")

    # Log Out Button
    st.button("Log Out", on_click=handle_logout)

    st.write("---")  # Separator

    # Headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json"
    }

    # Fetch and display files
    if 'files' not in st.session_state:
        # Fetch the list of files from the backend
        response = requests.get(
            f"{API_URL}/files",
            headers=headers
        )
        if response.status_code == 200:
            st.session_state.files = response.json()
        else:
            st.error("Error fetching files")
            st.session_state.files = []

    # File selection with placeholder
    if st.session_state.files:
        file_options = ['Select a PDF file'] + st.session_state.files
        file_name = st.selectbox("Select PDF File", file_options, index=0, key="file_selection")
        if file_name == 'Select a PDF file':
            file_name = None
    else:
        st.warning("No PDF files available.")
        file_name = None

    # Source content type selection with placeholder
    source_type_options = ['Select extraction method', 'opensource', 'cloudmersive_API']
    source_type = st.selectbox("Select Extraction Method", source_type_options, index=0, key="source_type_selection")
    if source_type == 'Select extraction method':
        source_type = None

    # Load and display extracted text when file and source_type are selected
    if file_name and source_type:
        # Fetch the extracted text from the backend
        params = {
            "file_name": file_name,
            "source_type": source_type
        }
        response = requests.get(
            f"{API_URL}/get-extracted-text",
            headers=headers,
            params=params
        )
        if response.status_code == 200:
            extracted_text = response.json().get("extracted_text", "")
            st.subheader("Extracted Text Preview")
            st.text_area("Extracted Text Content", extracted_text[:5000], height=300, disabled=True)
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            st.error(f"Error fetching extracted text: {error_detail}")
            extracted_text = ""
    else:
        extracted_text = ""

    # Actions
    if file_name and source_type:
        st.subheader("Actions")

        # Summarize PDF Section
        st.write("### Summarize PDF")
        if st.button("Summarize PDF"):
            if extracted_text.strip() == "":
                st.warning("No extracted text available to summarize.")
            else:
                with st.spinner('Summarizing the PDF...'):
                    # Summarize the PDF content
                    data = {
                        "file_name": file_name,
                        "source_type": source_type
                    }
                    response = requests.post(
                        f"{API_URL}/summarize",
                        headers=headers,
                        json=data
                    )
                if response.status_code == 200:
                    summary = response.json().get("summary")
                    st.subheader("Summary")
                    st.write(summary)
                else:
                    error_detail = response.json().get('detail', 'Unknown error')
                    st.error(f"Error: {error_detail}")

        st.write("---")  # Separator

        # Ask a Question Section
        st.write("### Ask a Question about the PDF")
        question = st.text_area("Enter your question here", key="question_input")
        if st.button("Submit Question"):
            if not question.strip():
                st.warning("Please enter a question.")
            else:
                with st.spinner('Answering your question...'):
                    data = {
                        "file_name": file_name,
                        "source_type": source_type,
                        "question": question
                    }
                    # Send the request to the backend
                    response = requests.post(
                        f"{API_URL}/ask-question",
                        headers=headers,
                        json=data
                    )
                if response.status_code == 200:
                    assistant_reply = response.json().get("answer")
                    st.subheader("Answer:")
                    st.write(assistant_reply)
                else:
                    error_detail = response.json().get('detail', 'Unknown error')
                    st.error(f"Error: {error_detail}")
    else:
        st.info("Please select a PDF file and extraction method to proceed.")

def main():
    if st.session_state.page == "signin":
        login()
    elif st.session_state.page == "signup":
        register()
    elif st.session_state.page == "home":
        if st.session_state.logged_in:
            home()
        else:
            st.session_state.page = "signin"
            login()

if __name__ == "__main__":
    main()