import glob
import json
import math
from datetime import date, datetime
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

openai_api_key = os.getenv("OPENAI_API_KEY")
openai_model = os.getenv("OPENAI_API_MODEL")

client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "<your OpenAI API key if not set as env var>"))

st.set_page_config(
    initial_sidebar_state="collapsed",
    page_title="Tourists Assistant Chatbot - Build Knowledge",
    page_icon=":earth_asia:"
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


def do_fine_tuning():
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

        response = client.fine_tuning.jobs.create(
            training_file=training_file_id,
            validation_file=validation_file_id,
            model="gpt-3.5-turbo",
            suffix=f"cttourism{datetime.now().strftime('%Y-%m-%d')}",
            # hyperparameters={
            #     "learning_rate": 1e-4,
            #     "batch_size": 4,
            #     "num_epochs": 3
            # }
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
        csv = os.path.split(file_csv_tuning)[1]
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
    for file_tuning in file_tuning_list:
        filename = os.path.split(file_tuning, )[1]

        st.write(f"Fine-tuning data *{filename}* is in progress...")

        pd.read_excel(file_tuning).to_csv(file_tuning.replace('xlsx', 'csv'), index=False)


def ui_rendering():
    st.markdown("<b>Fine-tuning GPT model</b>", unsafe_allow_html=True)

    st.caption("To update latest tourism information in Can Tho City.")

    with open("upload_files/fine_tuning_data/fine_tuning_data_template.xlsx", "rb") as template_file:
        template_byte = template_file.read()

    st.download_button(
        label="Download fine-tuning data template",
        data=template_byte,
        file_name="fine_tuning_data_template.xlsx"
    )

    training_data = st.file_uploader("*Upload file*", type=("xlsx", "xls"))

    if training_data:
        df = pd.read_excel(training_data)
        st.write(df)

    if st.button("Upload data"):
        st.write("Uploading training data...")
        if training_data:
            df = pd.read_excel(training_data)
            Path("upload_files/fine_tuning_data/in_progress").mkdir(exist_ok=True)
            df.to_excel(
                f"upload_files/fine_tuning_data/in_progress/{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}_{training_data.name}",
                index=False)
            st.write("Training data uploaded successfully.")

    if st.button("Start fine-tuning"):
        st.write("Fine-tuning is in progress...")

        convert_fine_tuning_data_to_csv()

        convert_fine_tuning_csv_to_jsonl()

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
