"""
CJ-AI — Cybersecurity AI Assistant
Entry point: run with `python main.py`
"""

import sys
from pathlib import Path

# Make sure the project root is in the Python path
sys.path.insert(0, str(Path(__file__).parent))

import config
from ui.console import Console
from core.chat import ChatEngine
from database.database import Database
from utils.logger import setup_logger


def main():
    setup_logger(config.LOG_FILE)

    console = Console()
    console.show_banner()

    db = Database(config.DB_FILE)
    db.initialize()

    user_id = db.get_or_create_user("default")
    chat = ChatEngine(db=db, user_id=user_id)

    console.print_info("Type your cybersecurity question. Type 'exit' or 'quit' to leave.\n")

    while True:
        try:
            user_input = console.get_input()

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q", "خروج"):
                console.print_info("\nGoodbye! Stay secure. 🔐")
                break

            response = chat.respond(user_input)
            console.print_response(response)

        except KeyboardInterrupt:
            console.print_info("\nGoodbye! Stay secure. 🔐")
            break

    db.close()


if __name__ == "__main__":
    main()
