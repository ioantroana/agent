import argparse
import logging

from agent import Agent
from logging_setup import setup_logging

logger = logging.getLogger("main")  # __name__ would be "__main__" when this file is run directly

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="A small coding agent.")
    parser.add_argument(
        "-m", "--message",
        help="Send one message, print the answer and exit. Without it, start an interactive chat.",
    )
    return parser.parse_args()

def run_once(agent: Agent, message: str) -> None:
    logger.info("User (one-shot): %s", message)
    agent.send(message)

def run_interactive(agent: Agent) -> None:
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
        logger.info("User: %s", user_input)
        agent.send(user_input)

def main() -> None:
    args = parse_args()
    log_file = setup_logging()
    logger.info("Session started, logging to %s", log_file)
    agent = Agent()

    if args.message:
        run_once(agent, args.message)
    else:
        run_interactive(agent)

    logger.info("Session finished")

if __name__ == "__main__":
    main()
