from st_pages import Page, Section, show_pages
import streamlit as st

st.set_page_config(page_title="Tourists Assistant Chatbot", page_icon=":earth_asia:")

show_pages(
    [
        Page("pages/0_Chat_Bot.py", "Tourists Assistant Chatbot", ":robot_face:"),

        # Section("Build Knowledge", ":brain:"),

        Page("pages/2_Fine_Tune.py", "Build Knowledge - Fine Tune GPT", ":building_construction:"),

        Page("pages/1_File_Q&A.py", "Build Knowledge - From File Resources", ":building_construction:")
        # # The pages appear in the order you pass them
        # Page("example_app/example_four.py", "Example Four", "📖"),
        # Page("example_app/example_two.py", "Example Two", "✏️"),
        # # Will use the default icon and name based on the filename if you don't
        # # pass them
        # Page("example_app/example_three.py"),
        # Page("example_app/example_five.py", "Example Five", "🧰"),
    ]
)

st.switch_page("pages/0_Chat_Bot.py")