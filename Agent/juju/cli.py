import sys

from juju.core.agent import AgentService


def main():
    agent = AgentService()
    while True:
        try:
            user_msg = input("You: ")
            if not user_msg.strip():
                continue
            print("Juju: ", end="", flush=True)
            agent.send_message(user_msg, on_content=lambda c: print(c, end="", flush=True))
            print()
        except EOFError:
            break
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
