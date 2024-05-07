from datetime import date
from pathlib import Path

import streamlit as st
import yaml
from streamlit_authenticator import Authenticate
from yaml.loader import SafeLoader
import pandas as pd

st.set_page_config(
    initial_sidebar_state="collapsed"
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


def ui_rendering():
    st.markdown("<b>Fine-tuning GPT model</b>", unsafe_allow_html=True)

    st.caption("To update latest tourism information in Can Tho City.")

    training_data = st.file_uploader("*Upload file*", type=("xlsx", "xls"))

    if training_data:
        df = pd.read_excel(training_data)
        st.write(df)
        Path("upload_files/fine_tuning_data/in_progress").mkdir(exist_ok=True)
        df.to_excel(f"upload_files/fine_tuning_data/in_progress/{date.today()}_{training_data.name}", index=False)

    if st.button("Start fine-tuning"):
        st.write("Fine-tuning is in progress...")

        st.write("Fine-tuning is completed.")

    # question = st.text_input(
    #     "Ask something about the article",
    #     placeholder="Can you give me a short summary?",
    #     disabled=not uploaded_file,
    # )

    # validation_data = st.file_uploader("*Upload a validation data*", type=("jsonl"))

    # if uploaded_file and question and not anthropic_api_key:
    #     st.info("Please add your Anthropic API key to continue.")
    #
    # if uploaded_file and question and anthropic_api_key:
    #     article = uploaded_file.read().decode()
    #     prompt = f"""{anthropic.HUMAN_PROMPT} Here's an article:\n\n<article>
    #     {article}\n\n</article>\n\n{question}{anthropic.AI_PROMPT}"""
    #
    #     client = anthropic.Client(api_key=anthropic_api_key)
    #     response = client.completions.create(
    #         prompt=prompt,
    #         stop_sequences=[anthropic.HUMAN_PROMPT],
    #         model="claude-v1",  # "claude-2" for Claude 2 model
    #         max_tokens_to_sample=100,
    #     )
    #     st.write("### Answer")
    #     st.write(response.completion)


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
