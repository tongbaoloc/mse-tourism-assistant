import streamlit as st
from dotenv import load_dotenv
import os

from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

st.set_page_config(
    initial_sidebar_state="collapsed",
    page_title="Tourists Assistant Chatbot",
    page_icon=":earth_asia:",
)

load_dotenv()

# openai_api_key = st.secrets["OPENAI_API_KEY"]
# openai_model = st.secrets["OPENAI_API_MODEL"]
development = os.getenv("DEVELOPMENT")

# openai_api_key = os.getenv("OPENAI_API_KEY")
openai_api_key = 'sk-proj-Woh8SFgZ0Z2kVew3diIYT3BlbkFJSpojO8dFcZCX1Lu24XdP'
openai_model = os.getenv("OPENAI_MODEL")
openai_temperature = os.getenv("OPENAI_TEMPERATURE")
openai_tokens = os.getenv("OPENAI_TOKENS")
openai_system_prompt = os.getenv("OPENAI_SYSTEM_PROMPT")
openai_sql_system_prompt = os.getenv("OPENAI_SQL_SYSTEM_PROMPT")
openai_welcome_prompt = os.getenv("OPENAI_WELCOME_PROMPT")
openai_fine_tune_model = os.getenv("OPENAI_FINE_TUNE_MODEL")
openai_fine_tune_training_data_set_percent = os.getenv("FINE_TUNE_TRAINING_DATA_SET_PERCENT")
# OPENAI_PROJECT = proj_XfVFbmxaGiC7DcFI1zhjPUNi
openai_organization = os.getenv("OPENAI_ORG_ID")
openai_project = os.getenv("OPENAI_PROJECT_ID")

fine_tune_secret = os.getenv("FINE_TUNE_SECRET")
chroma_path = os.getenv("CHROMA_PATH")

if development != "True":
    hide_menu_style = """
            <style>
            #MainMenu {visibility: hidden;}
            </style>
            """
    st.markdown(hide_menu_style, unsafe_allow_html=True)

st.markdown('<h3>Tourists Assistant Chatbot</h3>', unsafe_allow_html=True)
st.caption("This is a chatbot that can help you with your tourism queries. Ask me anything about Can Tho City!")

print(" 🚀 🚀 🚀 Environment Variables  🚀 🚀 🚀")
print("🚀  Development:", development)
print("⭐ OpenAI Organization Id:", openai_organization)
print("⭐ OpenAI Project:", openai_project)
print("⭐ OpenAI API Key:", openai_api_key)
print("⭐ OpenAI Model:", openai_model)
print("⭐ OpenAI Temperature:", openai_temperature)
print("⭐ OpenAI Tokens:", openai_tokens)
print("⭐ OpenAI System Prompt:", openai_system_prompt)
print("⭐ OpenAI Welcome Prompt:", openai_welcome_prompt)

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": openai_sql_system_prompt},
                                    {"role": "assistant", "content": openai_welcome_prompt}]

    print("🚀 🚀 🚀 Initial Session State 🚀 🚀 🚀")

    # print(st.session_state.messages)

for msg in st.session_state.messages:

    if msg["role"] != "system":
        st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():

    llm = ChatOpenAI(
        api_key=openai_api_key,
        openai_organization=openai_organization,
        model=openai_model,
        temperature=float(openai_temperature),
        max_tokens=int(openai_tokens),
    )

    # ConversationChain()

    st.session_state.messages.append({"role": "user", "content": prompt})

    st.chat_message("user").write(prompt)

    if development == "True":
        st.write("🚀 Development Environment")
        st.chat_message("system").write(st.session_state.messages)

    response = llm.invoke(st.session_state.messages)

    msg = response.content

    print("🚀 🚀 🚀 Prompt 🚀 🚀 🚀")

    print(st.session_state.messages)

    print("🚀 🚀 🚀 Real-time SQL Query 🚀 🚀 🚀")

    response = llm.invoke(st.session_state.messages)

    msg = response.content

    st.session_state.messages.append({"role": "assistant", "content": msg})

    st.chat_message("assistant").write(msg)
