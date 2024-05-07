from st_pages import Page, Section, add_page_title, show_pages

show_pages(
    [
        Page("pages/0_Chat_Bot.py", "Tourists Assistant Chatbot", ":robot_face:"),

        Section(name="Build Knowledge", icon=":brain:"),

        Page("pages/2_Fine_Tune.py", "Fine Tune GPT", ":building_construction:"),

        Page("pages/1_File_Q&A.py", "File resources", ":page_facing_up:")
        # # The pages appear in the order you pass them
        # Page("example_app/example_four.py", "Example Four", "📖"),
        # Page("example_app/example_two.py", "Example Two", "✏️"),
        # # Will use the default icon and name based on the filename if you don't
        # # pass them
        # Page("example_app/example_three.py"),
        # Page("example_app/example_five.py", "Example Five", "🧰"),
    ]
)

add_page_title()  # Optional method to add title and icon to current page
