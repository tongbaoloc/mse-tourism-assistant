import glob
from datetime import datetime
from pathlib import Path

import streamlit as st
import yaml
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_community.embeddings.openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from streamlit_authenticator import Authenticate
from yaml.loader import SafeLoader
import pandas as pd
import PyPDF2
from dotenv import load_dotenv
import os

load_dotenv()

development = os.getenv("DEVELOPMENT")

openai_api_key = os.getenv("OPENAI_API_KEY")
openai_model = os.getenv("OPENAI_API_MODEL")
openai_temperature = os.getenv("OPENAI_TEMPERATURE")
openai_tokens = os.getenv("OPENAI_TOKENS")
openai_system_prompt = os.getenv("OPENAI_SYSTEM_PROMPT")
openai_welcome_prompt = os.getenv("OPENAI_WELCOME_PROMPT")
openai_fine_tune_model = os.getenv("OPENAI_FINE_TUNE_MODEL")
openai_fine_tune_training_data_set_percent = os.getenv("FINE_TUNE_TRAINING_DATA_SET_PERCENT")
# OPENAI_PROJECT = proj_XfVFbmxaGiC7DcFI1zhjPUNi
openai_organization = os.getenv("OPENAI_ORG_ID")
openai_project = os.getenv("OPENAI_PROJECT_ID")

fine_tune_secret = os.getenv("FINE_TUNE_SECRET")
chroma_path = os.getenv("CHROMA_PATH")

RAG_PDF_FILES = "upload_files/rag_files/pdf"

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


def move_file_to_completed_folder(file_name):
    Path("upload_files/fine_tuning_data/completed").mkdir(exist_ok=True)
    os.rename(file_name, f"upload_files/fine_tuning_data/completed/{os.path.split(file_name)[1]}")


def populate_rag_database(rag_file):
    # Create (or update) the data store.
    documents = load_documents()

    print(f"📚 Number of documents: {len(documents)}")

    chunks = split_documents(documents)

    add_to_chroma(chunks)


def add_to_chroma(chunks: list[Document]):
    # Instantiate the OpenAIEmbeddings class
    # print("✅ current chunks " + chunks.__str__() + " ✅")
    # Load the existing database.
    db = Chroma(
        persist_directory=chroma_path,
        embedding_function=OpenAIEmbeddings()
    )

    # Calculate Page IDs.
    chunks_with_ids = calculate_chunk_ids(chunks)

    # Add or Update the documents.
    existing_items = db.get(include=[])  # IDs are always included by default
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    # Only add documents that don't exist in the DB.
    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)

    if len(new_chunks):
        print(f"👉 Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        db.add_documents(new_chunks, ids=new_chunk_ids)
        db.persist()
    else:
        print("✅ No new documents to add")


def calculate_chunk_ids(chunks):
    # This will create IDs like "data/monopoly.pdf:6:2"
    # Page Source : Page Number : Chunk Index

    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        # If the page ID is the same as the last one, increment the index.
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        # Calculate the chunk ID.
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        # Add it to the page meta-data.
        chunk.metadata["id"] = chunk_id

    return chunks


def load_documents():
    document_loader = PyPDFDirectoryLoader(RAG_PDF_FILES)
    return document_loader.load()


def split_documents(documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=80,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)


def ui_rendering():
    st.markdown("<h3>Building Knowledge Sources</h3>", unsafe_allow_html=True)

    st.caption("Search relevant information from multiple data sources, such as PDF, PowerPoint, and MD files.")

    st.info("Adding data sources.")

    # TODO: support PDF files for now
    # rag_files = st.file_uploader("Choose files", type=("pdf", "md", "xlsx"), accept_multiple_files=True)
    rag_files = st.file_uploader("Choose files", type="pdf", accept_multiple_files=True)

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
                    f"{rag_sheet_path}/{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}_{rag_file.name}",
                    index=False)
            elif rag_file.type == 'application/pdf':
                with open(os.path.join(rag_pdf_path, f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}_{rag_file.name}"), "wb") as f:
                    f.write(rag_file.getbuffer())
            elif rag_file.name.endswith('.md'):
                with open(os.path.join(rag_md_path, f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}_{rag_file.name}"), "wb") as f:
                    f.write(rag_file.getbuffer())

        st.write("RAG files uploaded successfully")

    st.info("Training RAG model.")

    if development == "True":
        fine_tuned_secret = st.text_input("Enter the secret to train RAG model", type="password", value="ABC123")
    else:
        fine_tuned_secret = st.text_input("Enter the secret to train RAG model", type="password")

    if st.button("**Train RAG model**"):

        if fine_tuned_secret != fine_tune_secret:
            st.error("Secret is incorrect.")
            return

        rag_file_list = glob.glob(RAG_PDF_FILES + "/*.pdf")

        st.write(f"RAG file list: {rag_file_list}")

        if not rag_file_list:
            st.write("No file to fine-tune.")
            return

        st.write("Training RAG model is in progress...")

        for rag_file in rag_file_list:

            st.write(f"Training RAG model with {rag_file}...")

            populate_rag_database(rag_file)

            move_file_to_completed_folder(rag_file)

        st.write("Training RAG model is completed successfully.")

    st.info("Uploaded files previewing")

    for rag_file in rag_files:
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
                # TODO: using the preview of the pdf content
                content += pdf_reader.pages[page].extract_text()
            # Display the content
            st.markdown(content)
        elif rag_file.name.endswith('.md'):
            df = pd.read_csv(rag_file)
            st.write(df, unsafe_allow_html=True)


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
