import streamlit as st
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

# Initialize session state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'token' not in st.session_state:
    st.session_state.token = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'page' not in st.session_state:
    st.session_state.page = "home"
if 'files' not in st.session_state:
    st.session_state.files = []
if 'summary' not in st.session_state:
    st.session_state.summary = None  # To store the summary
if 'answer' not in st.session_state:
    st.session_state.answer = None  # To store the answer to the question
if 'prev_file_name' not in st.session_state:
    st.session_state.prev_file_name = None  # To track changes in file selection
if 'prev_source_type' not in st.session_state:
    st.session_state.prev_source_type = None  # To track changes in extraction method
if 'question_answered' not in st.session_state:
    st.session_state.question_answered = False  # To control when to display the answer

def initial_home():
    # Set page layout to wide only on the home page
    st.set_page_config(page_title="PDF Summarizer and Q&A", page_icon="📄", layout="wide")

    # Apply custom CSS to center the content
    st.markdown(
        """
        <style>
        /* Center the main content */
        .main .block-container {
            max-width: 80%;
            padding-top: 1rem; /* Reduced padding */
            padding-left: 5%;
            padding-right: 5%;
            margin-left: auto;
            margin-right: auto;
        }
        /* Style for features list */
        .features {
            font-size: 1rem; /* Reduced from 1.2rem */
            margin-left: 1.5rem; /* Reduced margin */
        }
        .features li {
            margin-bottom: 0.3rem; /* Reduced spacing */
        }
        /* Style for the footer */
        .footer {
            text-align: center;
            font-size: 0.9rem; /* Reduced font size */
            color: #888888;
            margin-top: 1.5rem; /* Reduced margin */
        }
        /* Style for buttons */
        .stButton > button {
            background-color: #4CAF50;
            color: white;
            padding: 0.4rem 0.8rem; /* Reduced padding */
            margin: 0.4rem 0;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .stButton > button:hover {
            background-color: #45a049;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Create columns to position the login button at the top right
    col1, col2 = st.columns([8, 1])  # Adjusted column widths

    def go_to_signin():
        st.session_state.page = "signin"

    with col2:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        st.button("🔒 Login", key="login_button", on_click=go_to_signin)

    # Display the application information with adjusted font sizes
    st.markdown(
        '<div style="text-align: center; font-size: 3.5rem; font-weight: bold;">📄 PDF Summarizer and Q&A</div>',
        unsafe_allow_html=True)
    st.markdown(
        '<div style="text-align: center; font-size: 2.5rem;">Your AI-powered assistant for PDF documents</div>',
        unsafe_allow_html=True)
    st.write("---")
    st.markdown(
        '<div style="text-align: center; font-size: 2.5rem;">✨ Features</div>',
        unsafe_allow_html=True)
    st.markdown('''
                <div style="text-align: center;
    <ul class="features">
        <li>🔍 <strong>Summarize</strong> PDF documents quickly and efficiently.</li>
        <li>💬 <strong>Ask questions</strong> about the content of PDFs.</li>
        <li>📂 <strong>Choose</strong> from a variety of preprocessed PDF extracts.</li>
        <li>⚙️ <strong>Use</strong> either Python OpenSource or Cloudmersive API extraction methods.</li>
    </ul>
    ''', unsafe_allow_html=True)
    st.write("---")
    st.markdown(
        '<div style="text-align: center; font-size: 2.5rem;">🚀 Get Started</div>',
        unsafe_allow_html=True)
    st.markdown('<p style="text-align:center;">Click the <strong>🔒 Login</strong> button at the top right to sign in or create a new account.</p>', unsafe_allow_html=True)
    st.markdown('<div class="footer">© 2024 PDF Summarizer and Q&A. All rights reserved.</div>', unsafe_allow_html=True)

def register():
    # Set default page layout
    st.set_page_config(page_title="Sign Up", page_icon="🔑")

    # Add a "Back" button at the top right to return to the sign-in page
    col1, col2 = st.columns([8, 1.5])  # Adjusted column widths

    with col1:
        st.markdown(
            '<div style="text-align: left; font-size: 3rem; font-weight: bold; margin-top: 1rem; margin-bottom: 1rem;">🔑 Sign Up</div>',
            unsafe_allow_html=True)
    with col2:
        st.button("🔙 Back", on_click=lambda: st.session_state.update(page="signin"))

    # Use unique keys for input fields
    st.write("Please fill in the details below to create a new account.")
    email = st.text_input("📧 Email", key="signup_email")
    username = st.text_input("👤 Username", key="signup_username")
    password = st.text_input("🔒 Password", type="password", key="signup_password")
    password_confirm = st.text_input("🔒 Confirm Password", type="password", key="signup_password_confirm")

    # Define callback functions
    def handle_register():
        if not email or not username or not password or not password_confirm:
            st.warning("⚠️ Please fill in all fields")
        elif password != password_confirm:
            st.warning("⚠️ Passwords do not match")
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
                st.success("🎉 Registration successful! Please sign in.")
                # Clear the input fields
                st.session_state.signup_email = ''
                st.session_state.signup_username = ''
                st.session_state.signup_password = ''
                st.session_state.signup_password_confirm = ''
                st.session_state.page = "signin"
            else:
                error_detail = response.json().get('detail', 'Unknown error')
                st.error(f"❌ Registration failed: {error_detail}")

    # Registration button
    st.button("✅ Register", on_click=handle_register)

def login():
    # Set default page layout
    st.set_page_config(page_title="Sign In", page_icon="🔐")

    # Add a "Back" button at the top right to return to the welcome page
    col1, col2 = st.columns([8, 1.5])  # Adjusted column widths

    with col1:
        st.markdown(
            '<div style="text-align: left; font-size: 3rem; font-weight: bold; margin-top: 1rem; margin-bottom: 1rem;">🔐 Sign In</div>',
            unsafe_allow_html=True)
    with col2:
        st.button("🔙 Back", on_click=lambda: st.session_state.update(page="home"))

    st.write("Please enter your credentials to sign in.")

    # Use unique keys for input fields
    username = st.text_input("👤 Username", key="signin_username")
    password = st.text_input("🔒 Password", type="password", key="signin_password")

    # Define callback functions
    def handle_login():
        if not username or not password:
            st.warning("⚠️ Please enter both username and password")
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
                # Clear the input fields
                st.session_state.signin_username = ''
                st.session_state.signin_password = ''
                st.session_state.page = "dashboard"
                st.success("✅ Logged in successfully!")
            else:
                error_detail = response.json().get('detail', 'Unknown error')
                st.error(f"❌ Login failed: {error_detail}")

    def go_to_signup():
        # Clear the input fields when switching pages
        st.session_state.signin_username = ''
        st.session_state.signin_password = ''
        st.session_state.page = "signup"

    st.button("➡️ Sign In", on_click=handle_login)
    st.write("Don't have an account?")
    st.button("📝 Sign Up", on_click=go_to_signup)

def home():
    # Set default page layout
    st.set_page_config(page_title="Dashboard", page_icon="📄")

    # Adjusted column widths to accommodate the "Logout" button text
    col1, col2 = st.columns([8, 1.5])  # Adjusted column widths

    with col1:
        # Adjusted font sizes to make the headings smaller
        st.markdown(
            '<div style="text-align: left; font-size: 2.5rem; font-weight: bold;">📄 PDF Summarizer and Q&A</div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div style="text-align: left; font-size: 2rem;">Welcome, {st.session_state.username}!</div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div style="text-align: left; font-size: 2rem;">Select a PDF file and choose an action.</div>',
            unsafe_allow_html=True)
    with col2:
        st.button("🚪 Logout", on_click=lambda: st.session_state.update(
            logged_in=False, token=None, username=None, page="home", summary=None, answer=None,
            prev_file_name=None, prev_source_type=None, question_answered=False, question_input=''
        ))

    st.write("---")  # Separator

    # Create a placeholder for the message
    message_placeholder = st.empty()

    # Headers for authenticated requests
    headers = {
        "Authorization": f"Bearer {st.session_state.token}",
        "Content-Type": "application/json"
    }

    # Fetch and display files
    if not st.session_state.files:
        # Fetch the list of files from the backend
        response = requests.get(
            f"{API_URL}/files",
            headers=headers
        )
        if response.status_code == 200:
            st.session_state.files = response.json()
        else:
            st.error("❌ Error fetching files")
            st.session_state.files = []

    # Initialize variables
    file_name = None
    source_type = None

    # Mapping between display names and backend values
    source_type_display_options = ['Select extraction method', 'Python OpenSource', 'Cloudmersive API']
    source_type_mapping = {
        'Python OpenSource': 'opensource',
        'Cloudmersive API': 'cloudmersive_API'
    }

    # File selection with placeholder
    if st.session_state.files:
        file_options = ['Select a PDF file'] + st.session_state.files
        file_name = st.selectbox("📄 Select PDF File", file_options, index=0, key="file_selection")
        if file_name == 'Select a PDF file':
            file_name = None
    else:
        st.warning("⚠️ No PDF files available.")

    # Source content type selection with mapping
    source_type_display = st.selectbox(
        "⚙️ Select Extraction Method",
        source_type_display_options,
        index=0,
        key="source_type_selection"
    )
    if source_type_display == 'Select extraction method':
        source_type = None
    else:
        source_type = source_type_mapping[source_type_display]

    # After the selection widgets, check if both are selected
    if not file_name or not source_type:
        # Display the message in the placeholder
        message_placeholder.info("ℹ️ Please select a PDF file and extraction method to proceed.")
        # Clear summary and answer when selections change
        st.session_state.summary = None
        st.session_state.answer = None
        st.session_state.question_input = ''
        st.session_state.question_answered = False
        st.session_state.prev_file_name = None
        st.session_state.prev_source_type = None
    else:
        # Check if the file_name or source_type has changed
        if (file_name != st.session_state.prev_file_name) or (source_type != st.session_state.prev_source_type):
            # The selection has changed, clear summary and answer
            st.session_state.summary = None
            st.session_state.answer = None
            st.session_state.question_input = ''
            st.session_state.question_answered = False
        # Update the previous selections
        st.session_state.prev_file_name = file_name
        st.session_state.prev_source_type = source_type
        # Clear the message placeholder
        message_placeholder.empty()

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
            st.subheader("📝 Extracted Text Preview")
            st.text_area("Extracted Text Content", extracted_text[:5000], height=300, disabled=True)
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            st.error(f"❌ Error fetching extracted text: {error_detail}")
            extracted_text = ""
    else:
        extracted_text = ""

    st.write("---")  # Separator

    # Actions
    if file_name and source_type:
        st.subheader("⚡ Actions")

        # Summarize PDF Section
        st.write("### 📚 Summarize PDF")
        if st.button("📝 Summarize PDF"):
            if extracted_text.strip() == "":
                st.warning("⚠️ No extracted text available to summarize.")
            else:
                with st.spinner('🔄 Summarizing the PDF...'):
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
                    st.session_state.summary = summary  # Store the summary in session state
                    st.success("✅ Summary generated successfully!")
                else:
                    error_detail = response.json().get('detail', 'Unknown error')
                    st.error(f"❌ Error: {error_detail}")

        # Display the summary if it exists
        if st.session_state.summary:
            st.subheader("📄 Summary")
            st.write(st.session_state.summary)

        st.write("---")  # Separator

        # Ask a Question Section
        st.write("### ❓ Ask a Question")
        question = st.text_area("💭 Enter your question here", key="question_input")
        if st.button("➡️ Submit Question"):
            if not question.strip():
                st.warning("⚠️ Please enter a question.")
            else:
                with st.spinner('🔄 Answering your question...'):
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
                    st.session_state.answer = assistant_reply  # Store the answer in session state
                    st.session_state.question_answered = True
                    st.success("✅ Question answered successfully!")
                else:
                    error_detail = response.json().get('detail', 'Unknown error')
                    st.error(f"❌ Error: {error_detail}")
                    st.session_state.answer = None
                    st.session_state.question_answered = False

        # Display the answer if it exists
        if st.session_state.answer and st.session_state.question_answered:
            st.subheader("💡 Answer")
            st.write(st.session_state.answer)

def main():
    if st.session_state.page == "home":
        initial_home()
    elif st.session_state.page == "signin":
        login()
    elif st.session_state.page == "signup":
        register()
    elif st.session_state.page == "dashboard":
        if st.session_state.logged_in:
            home()
        else:
            st.session_state.page = "signin"

if __name__ == "__main__":
    main()