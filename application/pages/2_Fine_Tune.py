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
from wandb.integration.openai.fine_tuning import WandbLogger

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

st.set_page_config(
    initial_sidebar_state="collapsed",
    page_title="Tourists Assistant Chatbot - Fine Tune GPT",
    page_icon=":earth_asia:",
    # layout="wide"
)

# if development != "True":
#     hide_menu_style = """
#             <style>
#             #MainMenu {visibility: hidden;}
#             </style>
#             """
#     st.markdown(hide_menu_style, unsafe_allow_html=True)

client = openai.OpenAI(
    api_key=openai_api_key,
    organization=openai_organization)

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
            out.write(json.dumps(ddict) + "\n")


def move_files_to_completed_folder():
    # move all files from upload_files/fine_tuning_data/in_progress/ to upload_files/fine_tuning_data/completed/
    file_tuning_list = glob.glob('upload_files/fine_tuning_data/in_progress/*')

    for file_tuning in file_tuning_list:
        Path("upload_files/fine_tuning_data/completed").mkdir(exist_ok=True)
        os.rename(file_tuning, f"upload_files/fine_tuning_data/completed/{os.path.split(file_tuning)[1]}")

    print("All files are moved to completed folder.")


def move_file_to_completed_folder(file_name):
    Path("upload_files/fine_tuning_data/completed").mkdir(exist_ok=True)
    os.rename(file_name, f"upload_files/fine_tuning_data/completed/{os.path.split(file_name)[1]}")


def do_fine_tuning(epochs_value=None, learning_rate_value=None, batch_size_value=None, fine_tuned_suffix=None,
                   sql_tunned=False):
    if sql_tunned is True:

        sql_file_tuning_list = glob.glob('upload_files/fine_tuning_data/in_progress/*.jsonl')

        training_file_id = None
        validation_file_id = None

        for sql_file_tuning in sql_file_tuning_list:

            st.write(f"SQL fine-tuning data *{sql_file_tuning}* is in progress...")

            with open(sql_file_tuning, "rb") as sql_fd:
                sql_response = client.files.create(
                    file=sql_fd,
                    purpose="fine-tune"
                )

            if "_training.jsonl" in sql_file_tuning:
                training_file_id = sql_response.id
            elif "_validation.jsonl" in sql_file_tuning:
                validation_file_id = sql_response.id

            # move_files_to_completed_folder()  # TODO: move only the processed files
            move_file_to_completed_folder(sql_file_tuning)

        response = create_fine_tuning_job(batch_size_value,
                                          epochs_value,
                                          fine_tuned_suffix,
                                          learning_rate_value,
                                          training_file_id,
                                          validation_file_id)

        response = client.fine_tuning.jobs.retrieve(response.id)

        print("Job ID:", response.id)
        print("Status:", response.status)
        print("Trained Tokens:", response.trained_tokens)

        if development == "True":
            st.write("Weight and Biases logging is in progress...")
            WandbLogger.sync(fine_tune_job_id=response.id,
                             project="tourism-assistant-sql",
                             openai_client=client,
                             wait_for_job_success=False,
                             tags=["tourism", "sql-fine-tuning"])

    else:
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

            response = create_fine_tuning_job(batch_size_value, epochs_value, fine_tuned_suffix, learning_rate_value,
                                              training_file_id, validation_file_id)

            response = client.fine_tuning.jobs.retrieve(response.id)

            print("Job ID:", response.id)
            print("Status:", response.status)
            print("Trained Tokens:", response.trained_tokens)

            if development == "True":
                st.write("Weight and Biases logging is in progress...")
                WandbLogger.sync(fine_tune_job_id=response.id,
                                 project="tourism-assistant",
                                 openai_client=client,
                                 tags=["tourism", "fine-tuning"],
                                 wait_for_job_success=False)

            # response = client.fine_tuning.jobs.list_events(response.id)

            # events = response.data
            # events.reverse()
            # Weight and Biases logging is in progress...
            # for event in events:
            #     print(event.message)

            # move_files_to_completed_folder()  # TODO: move only the processed files
            move_file_to_completed_folder(validation_file_name)
            move_file_to_completed_folder(training_file_name)


def create_fine_tuning_job(batch_size_value, epochs_value, fine_tuned_suffix, learning_rate_value, training_file_id,
                           validation_file_id):
    if epochs_value is not None and learning_rate_value is not None and batch_size_value is not None:

        response = client.fine_tuning.jobs.create(
            training_file=training_file_id,
            validation_file=validation_file_id,
            model=openai_fine_tune_model,
            suffix=f"{fine_tuned_suffix}",
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
            model=openai_fine_tune_model,
            suffix=f"{fine_tuned_suffix}"
        )
    return response


def convert_fine_tuning_csv_to_jsonl():
    file_tuning_csv_list = glob.glob('upload_files/fine_tuning_data/in_progress/*.csv')

    for file_csv_tuning in file_tuning_csv_list:
        tourism_df = pd.read_csv(file_csv_tuning)

        number_of_training_row = math.floor(len(tourism_df.index) * float(openai_fine_tune_training_data_set_percent))

        number_of_validate_row = len(tourism_df.index) - number_of_training_row

        training_df = tourism_df.loc[0:number_of_training_row]

        training_data = training_df.apply(prepare_example_conversation, axis=1).tolist()

        validation_df = tourism_df.loc[++number_of_validate_row:]

        validation_data = validation_df.apply(prepare_example_conversation, axis=1).tolist()

        write_jsonl(training_data, file_csv_tuning.replace(".csv", "_training.jsonl"))

        write_jsonl(validation_data, file_csv_tuning.replace(".csv", "_validation.jsonl"))


def create_user_message(row):
    return f"""Question: {row['ask']}"""


def prepare_example_conversation(row):
    messages = [{"role": "system", "content": openai_system_prompt}]

    user_message = create_user_message(row)

    messages.append({"role": "user", "content": user_message})

    messages.append({"role": "assistant", "content": row["answer"]})

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
    st.markdown("<h3>Fine-Tuning GPT on Custom Dataset</h3>", unsafe_allow_html=True)

    st.info("Fine-Tuning template files")

    st.caption("To update latest tourism information in Can Tho City.")

    with open("upload_files/fine_tuning_data/fine_tuning_ask_and_answer_template.xlsx", "rb") as aa_template_file:
        aa_template_byte = aa_template_file.read()

    st.download_button(
        label="Download the Q&A template",
        data=aa_template_byte,
        file_name="fine_tuning_ask_and_answer_template.xlsx"
    )

    st.write("Q&A example example:")

    aa_template_file = pd.read_excel("upload_files/fine_tuning_data/fine_tuning_ask_and_answer_template.xlsx")
    st.write(aa_template_file)

    with open("upload_files/fine_tuning_data/fine_tuning_sql_tune_template.xlsx", "rb") as sql_fine_tune_template_file:
        sql_fine_tune_template_byte = sql_fine_tune_template_file.read()

    st.download_button(
        label="Download the SQL fine tune template",
        data=sql_fine_tune_template_byte,
        file_name="fine_tuning_sql_tune_template.xlsx"
    )

    st.write("SQL fine tune example:")

    sql_fine_tune_template_file = pd.read_excel("upload_files/fine_tuning_data/fine_tuning_sql_tune_template.xlsx")
    st.write(sql_fine_tune_template_file)

    st.info("**Upload the Fine-Tuning data**")

    training_data = st.file_uploader("Choose file", type=("xlsx", "xls"), key="training_data")
    # TODO: support multiple files

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

    sql_training_files = st.file_uploader("Choose files (training, validation))", type="jsonl", key="sql_training_data",
                                          accept_multiple_files=True)
    st.warning("Please make sure to upload sql based training and validation data in jsonl format.")

    if sql_training_files:

        if st.button("Upload training/validation files"):
            st.write("Uploading sql training/validation data in jsonl format...")

            for sql_training_file in sql_training_files:
                Path("upload_files/fine_tuning_data/in_progress").mkdir(exist_ok=True)
                with open(f"upload_files/fine_tuning_data/in_progress/{sql_training_file.name}", "wb") as sql_fd:
                    sql_fd.write(sql_training_file.read())

            st.write("SQL training/validation data uploaded successfully.")

    st.info("**Create a Fine tuned model**")

    is_hyper_params = st.checkbox(" Do you want to adjust hyperparameters?")

    epochs_value = st.select_slider("Select the number of epochs", options=[1, 2, 3, 4, 5], value=2)

    st.write(f"Number of epochs: {epochs_value}")

    learning_rate_value = st.select_slider("Select the learning rate", options=[0.1, 0.2, 0.3, 0.4, 0.5], value=0.2)

    st.write(f"Learning rate: {learning_rate_value}")

    batch_size_value = st.select_slider("Select the batch size", options=[1, 2, 3, 4, 5], value=2)

    st.write(f"Batch size: {batch_size_value}")

    st.warning("Make sure to adjust the hyperparameters/data set properly to avoid overwriting or underwriting the "
               "model.")

    fine_tuned_suffix = st.text_input("Enter the suffix for the fine-tuned model",
                                      value=f"tourism{datetime.now().strftime('%Y-%m-%d')}")

    fine_tuned_secret = st.text_input("Enter the secret to fine-tune the model", type="password")

    sql_tunned = st.checkbox("Do you want to fine-tune the model with SQL based tune?")

    if st.button("**Start fine-tuning**"):

        if fine_tuned_secret != fine_tune_secret:
            st.error("Finetune secret is incorrect.")
            return

        file_tuning_list = glob.glob('upload_files/fine_tuning_data/in_progress/*')

        if not file_tuning_list:
            st.write("No file to fine-tune.")
            return

        if sql_tunned is True:
            st.write("SQL fine-tuning is in progress...")
        else:
            st.write("Fine-tuning is in progress...")

            convert_fine_tuning_data_to_csv()
            convert_fine_tuning_csv_to_jsonl()

        if is_hyper_params is True:
            do_fine_tuning(epochs_value, learning_rate_value, batch_size_value, fine_tuned_suffix, sql_tunned)
        else:
            do_fine_tuning(fine_tuned_suffix=fine_tuned_suffix, sql_tunned=sql_tunned)

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
