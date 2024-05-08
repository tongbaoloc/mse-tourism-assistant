from datetime import datetime
from pathlib import Path

import streamlit as st
import yaml
from streamlit_authenticator import Authenticate
from yaml.loader import SafeLoader
import os
import pandas as pd
import PyPDF2

st.set_page_config(
    initial_sidebar_state="collapsed",
    page_title="Tourists Assistant Chatbot - Build Knowledge",
    page_icon=":earth_asia:",
    # layout="wide"
)

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

development = os.getenv("DEVELOPMENT")
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_model = os.getenv("OPENAI_API_MODEL")
openai_temperature = os.getenv("OPENAI_TEMPERATURE")
openai_tokens = os.getenv("OPENAI_TOKENS")
openai_system_prompt = os.getenv("OPENAI_SYSTEM_PROMPT")
openai_welcome_prompt = os.getenv("OPENAI_WELCOME_PROMPT")

if development != "True":
    hide_menu_style = """
            <style>
            #MainMenu {visibility: hidden;}
            </style>
            """
    st.markdown(hide_menu_style, unsafe_allow_html=True)

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# passwords_to_hash = ['123123']
# hashed_passwords = Hasher(passwords_to_hash).generate()
#
# print(hashed_passwords)

authenticator = Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)

name, authentication_status, username = authenticator.login()


def ui_rendering():
    st.markdown("<h3>Building Knowledge Sources</h3>", unsafe_allow_html=True)

    st.caption("Search relevant information from multiple data sources, such as PDF, PowerPoint, and MD files.")

    rag_files = st.file_uploader("Choose files", type=("pdf", "md", "xlsx"), accept_multiple_files=True)

    if st.button("Upload files"):
        st.write("Uploading RAG files...")

        rag_repository_path = "upload_files/rag_files"
        rag_sheet_path = f"{rag_repository_path}/sheet"
        rag_pdf_path = f"{rag_repository_path}/pdf"
        rag_md_path = f"{rag_repository_path}/md"

        Path(rag_sheet_path).mkdir(exist_ok=True)
        Path(rag_pdf_path).mkdir(exist_ok=True)
        Path(rag_md_path).mkdir(exist_ok=True)

        for rag_file in rag_files:
            if rag_file.type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                df = pd.read_excel(rag_file)
                df.to_excel(
                    f"{rag_sheet_path}/{rag_file.name}",
                    index=False)
            elif rag_file.type == 'application/pdf':
                with open(os.path.join(rag_pdf_path, rag_file.name), "wb") as f:
                    f.write(rag_file.getbuffer())
            elif rag_file.name.endswith('.md'):
                with open(os.path.join(rag_md_path, rag_file.name), "wb") as f:
                    f.write(rag_file.getbuffer())

        st.write("RAG files uploaded successfully")

    st.divider()
    st.markdown("<h4>Uploaded files previewing</h4>", unsafe_allow_html=True)

    for rag_file in rag_files:
        st.divider()
        st.write(f"File name: {rag_file.name}")

        if rag_file.type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
            df = pd.read_excel(rag_file)
            st.write(df)
        elif rag_file.type == 'application/pdf':
            # Read the PDF file 1
            pdf_reader = PyPDF2.PdfReader(rag_file)
            # Extract the content
            content = ""
            for page in range(len(pdf_reader.pages)):
                content += pdf_reader.pages[page].extract_text()
            # Display the content
            st.markdown(content)
        elif rag_file.name.endswith('.md'):
            df = pd.read_csv(rag_file)
            st.markdown(df, unsafe_allow_html=True)


if st.session_state["authentication_status"]:
    # try:
    #     if authenticator.reset_password(st.session_state["username"]):
    #         with open('config.yaml', 'w') as file:
    #             yaml.dump(config, file, default_flow_style=False)
    #         st.success('Password modified successfully')
    #
    # except Exception as e:
    #     st.error(e)
    authenticator.logout()
    # st.write(f'Welcome *{st.session_state["name"]}*')
    ui_rendering()


elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
