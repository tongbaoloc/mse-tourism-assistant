from st_pages import Page, add_page_title, show_pages

show_pages(
    [
        Page("application/pages/0_Chat_Bot.py", "Chat Bot", ":chart_with_upwards_trend:"),
        Page("application/pages/1_File_Q&A.py", "Build Knowledge", ":books:"),
        Page("application/pages/2_Fine_Tune.py", "Fine Tune", ":books:")
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
