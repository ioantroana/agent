from agent import Agent

def main():
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
        agent.send(user_input)

if __name__ == "__main__":
    main()
