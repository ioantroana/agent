import logging

from agent import Agent
from logging_setup import setup_logging

logger = logging.getLogger(__name__)

def main():
    setup_logging()
    logger.info("Session started")
    agent = Agent()

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

    logger.info("Session finished")

if __name__ == "__main__":
    main()
