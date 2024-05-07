from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv
import os

st.set_page_config(
    initial_sidebar_state="collapsed",
    page_title="Tourists Assistant Chatbot",
    page_icon=":earth_asia:"
)

load_dotenv()

# openai_api_key = st.secrets["OPENAI_API_KEY"]
# openai_model = st.secrets["OPENAI_API_MODEL"]
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_model = os.getenv("OPENAI_API_MODEL")

st.title("Tourists Assistant Chatbot")
# st.caption("")
st.write("This is a chatbot that can help you with your tourism queries. Ask me anything about Can Tho City!")
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": "You are an expert in providing travel assistance "
                                                                  "for Can Tho. Your role is to offer detailed "
                                                                  "information, tips, and guidance to travelers "
                                                                  "interested in exploring Can Tho, Vietnam. You "
                                                                  "provide insights into the best places to visit, "
                                                                  "local cuisine, cultural highlights, and practical "
                                                                  "travel advice to ensure visitors have a memorable "
                                                                  "and smooth experience in Can Tho."},
                                    {"role": "assistant", "content": "A warm and vibrant welcome awaits you in Can "
                                                                     "Tho City. How can I assist you with your "
                                                                     "exploration?"}]
for msg in st.session_state.messages:
    # and "role" in st.session_state.messages[-1] and st.session_state.messages[-1]["role"] == "assistant"
    if msg["role"] != "system":
        st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    client = OpenAI(api_key=openai_api_key)
    st.session_state.messages.append({"role": "user", "content": prompt})

    st.chat_message("user").write(prompt)

    # check only on development environment

    # st.chat_message("send2gpt").write(st.session_state.messages)
    print(st.session_state.messages)

    response = client.chat.completions.create(model="ft:gpt-3.5-turbo-0125:personal:cantho-tourist:9LrBsXPX",
                                              messages=st.session_state.messages)
    msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
