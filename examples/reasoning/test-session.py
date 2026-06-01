"""Test the reasoning module with a sequence of sign labels."""

from dotenv import load_dotenv

from reasoning import create_session

load_dotenv()


session = create_session()

signs = ["Stop", "Speed-Limit-30", "Must-Turn-Left"]

for sign in signs:
    print(f"\n--- Detected: {sign} ---")
    response = session.ask(sign)
    print(response)
