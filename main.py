import argparse
import logging

from agent import Agent
from logging_setup import setup_logging
from terminal_ui import TerminalUI

logger = logging.getLogger("main")  # __name__ would be "__main__" when this file is run directly

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="A small coding agent.")
    parser.add_argument(
        "-m",
        "--message",
        help="Send one message, print the answer and exit. Without it, start an interactive chat.",
    )
    return parser.parse_args()

def _run_once(agent: Agent, message: str) -> None:
    logger.info(f"User (one-shot): {message}")
    agent.send(message)

def _run_interactive(agent: Agent) -> None:
    while True:
        try:
            user_input = input("> ")
        except (KeyboardInterrupt, EOFError):
            print("\nFinished session")
            break

        if user_input == "exit" or user_input == "":
            print("Finished session")
            break

        print("User: " + user_input)
        logger.info(f"User: {user_input}")
        agent.send(user_input)

def main() -> None:
    args = _parse_args()
    log_file = setup_logging()
    logger.info(f"Session started, logging to {log_file}")
    agent = Agent(TerminalUI())

    if args.message:
        _run_once(agent, args.message)
    else:
        _run_interactive(agent)

    logger.info("Session finished")

if __name__ == "__main__":
    main()
