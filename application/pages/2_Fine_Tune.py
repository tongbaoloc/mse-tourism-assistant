import glob
import json
import math
from datetime import datetime
import openai
from pathlib import Path

import streamlit as st
import yaml
from streamlit_authenticator import Authenticate
from yaml.loader import SafeLoader
import pandas as pd
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

if development != "True":
    hide_menu_style = """
            <style>
            #MainMenu {visibility: hidden;}
            </style>
            """
    st.markdown(hide_menu_style, unsafe_allow_html=True)

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

st.set_page_config(
    initial_sidebar_state="collapsed",
    page_title="Tourists Assistant Chatbot - Fine Tune GPT",
    page_icon=":earth_asia:",
    # layout="wide"
)

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


def write_jsonl(data_list: list, filename: str) -> None:
    with open(filename, "w") as out:
        for ddict in data_list:
            jout = json.dumps(ddict) + "\n"
            out.write(jout)


def move_files_to_completed_folder():
    # move all files from upload_files/fine_tuning_data/in_progress/ to upload_files/fine_tuning_data/completed/
    file_tuning_list = glob.glob('upload_files/fine_tuning_data/in_progress/*')

    for file_tuning in file_tuning_list:
        Path("upload_files/fine_tuning_data/completed").mkdir(exist_ok=True)
        os.rename(file_tuning, f"upload_files/fine_tuning_data/completed/{os.path.split(file_tuning)[1]}")

    print("All files are moved to completed folder.")


def do_fine_tuning(epochs_value=None, learning_rate_value=None, batch_size_value=None):
    file_tuning_list = glob.glob('upload_files/fine_tuning_data/in_progress/*.xlsx')
    for file_tuning in file_tuning_list:

        training_file_name = file_tuning.replace(".xlsx", "_training.jsonl")
        validation_file_name = file_tuning.replace(".xlsx", "_validation.jsonl")

        with open(training_file_name, "rb") as training_fd:
            training_response = client.files.create(
                file=training_fd, purpose="fine-tune"
            )

        training_file_id = training_response.id

        with open(validation_file_name, "rb") as validation_fd:
            validation_response = client.files.create(
                file=validation_fd, purpose="fine-tune"
            )
        validation_file_id = validation_response.id

        print("Training file ID:", training_file_id)
        print("Validation file ID:", validation_file_id)

        if epochs_value is not None and learning_rate_value is not None and batch_size_value is not None:
            response = client.fine_tuning.jobs.create(
                training_file=training_file_id,
                validation_file=validation_file_id,
                model="gpt-3.5-turbo-0125",
                suffix=f"tourism{datetime.now().strftime('%Y-%m-%d')}",
                hyperparameters={
                    "learning_rate": learning_rate_value,
                    "batch_size": batch_size_value,
                    "num_epochs": epochs_value
                }
            )
        else:
            response = client.fine_tuning.jobs.create(
                training_file=training_file_id,
                validation_file=validation_file_id,
                model="gpt-3.5-turbo-0125",
                suffix=f"tourism{datetime.now().strftime('%Y-%m-%d')}",
                integrations=[{
                    "type": "wandb",
                    "wandb": {
                        "project": "tourism-assistant",
                        "tags": ["tourism", "fine-tuning"]
                    }
                }]
            )

        move_files_to_completed_folder()

        print("Job ID:", response.id)
        print("Status:", response.status)

        response = client.fine_tuning.jobs.retrieve(response.id)

        print("Job ID:", response.id)
        print("Status:", response.status)
        print("Trained Tokens:", response.trained_tokens)

        response = client.fine_tuning.jobs.list_events(response.id)

        events = response.data
        events.reverse()

        for event in events:
            print(event.message)


def convert_fine_tuning_csv_to_jsonl():
    file_tuning_csv_list = glob.glob('upload_files/fine_tuning_data/in_progress/*.csv')
    for file_csv_tuning in file_tuning_csv_list:
        tourism_df = pd.read_csv(file_csv_tuning)

        number_of_training_row = math.floor(len(tourism_df.index) * 0.8)
        number_of_validate_row = len(tourism_df.index) - number_of_training_row

        training_df = tourism_df.loc[0:number_of_training_row]

        training_data = training_df.apply(prepare_example_conversation, axis=1).tolist()

        validation_df = tourism_df.loc[++number_of_validate_row:]

        validation_data = validation_df.apply(prepare_example_conversation, axis=1).tolist()

        write_jsonl(training_data, file_csv_tuning.replace(".csv", "_training.jsonl"))

        write_jsonl(validation_data, file_csv_tuning.replace(".csv", "_validation.jsonl"))


def create_user_message(row):
    return f"""Question: {row['Question']}"""


system_message = ("You are an expert in providing travel assistance for Can Tho. Your role is to offer detailed "
                  "information, tips, and guidance to travelers interested in exploring Can Tho, Vietnam. You provide "
                  "insights into the best places to visit, local cuisine, cultural highlights, and practical travel "
                  "advice to ensure visitors have a memorable and smooth experience in Can Tho.")


def prepare_example_conversation(row):
    messages = [{"role": "system", "content": system_message}]

    user_message = create_user_message(row)

    messages.append({"role": "user", "content": user_message})

    messages.append({"role": "assistant", "content": row["Answer"]})

    return {"messages": messages}


def convert_fine_tuning_data_to_csv():
    file_tuning_list = glob.glob('upload_files/fine_tuning_data/in_progress/*.xlsx')

    if not file_tuning_list:
        st.write("No file to fine-tune.")
        return

    for file_tuning in file_tuning_list:
        filename = os.path.split(file_tuning, )[1]

        st.write(f"Fine-tuning data *{filename}* is in progress...")

        pd.read_excel(file_tuning).to_csv(file_tuning.replace('xlsx', 'csv'), index=False)


def ui_rendering(special_internal_function=None):
    st.markdown("<h3>Fine-tuning GPT model</h3>", unsafe_allow_html=True)

    st.caption("To update latest tourism information in Can Tho City.")

    with open("upload_files/fine_tuning_data/fine_tuning_data_template.xlsx", "rb") as template_file:
        template_byte = template_file.read()

    st.write("*Download the fine-tuning data template*")

    st.download_button(
        label="Download",
        data=template_byte,
        file_name="fine_tuning_data_template.xlsx"
    )

    st.divider()

    st.write("*Upload the fine-tuning data*")

    training_data = st.file_uploader("Choose file", type=("xlsx", "xls"))

    if training_data:
        df = pd.read_excel(training_data)
        st.write(df)

    if st.button("Upload file"):
        st.write("Uploading training data...")
        if training_data:
            df = pd.read_excel(training_data)
            Path("upload_files/fine_tuning_data/in_progress").mkdir(exist_ok=True)
            df.to_excel(
                f"upload_files/fine_tuning_data/in_progress/{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}_{training_data.name}",
                index=False)
            st.write("Training data uploaded successfully.")

    st.divider()

    st.write("*Create a fine-tuned model*")

    is_hyper_params = st.checkbox(" Do you want to adjust hyperparameters?")

    epochs_value = st.select_slider("Select the number of epochs", options=[1, 2, 3, 4, 5], value=2)

    st.write(f"Number of epochs: {epochs_value}")

    learning_rate_value = st.select_slider("Select the learning rate", options=[0.1, 0.2, 0.3, 0.4, 0.5], value=0.2)

    st.write(f"Learning rate: {learning_rate_value}")

    batch_size_value = st.select_slider("Select the batch size", options=[1, 2, 3, 4, 5], value=2)

    st.write(f"Batch size: {batch_size_value}")

    if st.button("Start fine-tuning"):

        file_tuning_list = glob.glob('upload_files/fine_tuning_data/in_progress/*.xlsx')

        if not file_tuning_list:
            st.write("No file to fine-tune.")
            return

        st.write("Fine-tuning is in progress...")

        convert_fine_tuning_data_to_csv()

        convert_fine_tuning_csv_to_jsonl()

        if is_hyper_params is True:
            print(epochs_value, learning_rate_value, batch_size_value)
            do_fine_tuning(epochs_value, learning_rate_value, batch_size_value)
        else:
            do_fine_tuning()

        st.write("Fine-tuning is submitted successfully. Please check the status in your OpenAI account.")


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
