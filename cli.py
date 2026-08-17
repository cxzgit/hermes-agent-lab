"""Interactive CLI: read input, call the Agent, and retain history."""

from __future__ import annotations

from run_agent import AIAgent


class HermesCLI:
    def __init__(
        self,
        *,
        model: str,
        base_url: str,
        client=None,
    ) -> None:
        # Reuse one Agent throughout this CLI session.
        self.agent = AIAgent(model=model, base_url=base_url, client=client)
        self.conversation_history: list[dict[str, str]] = []

    def run(self) -> None:
        print("[2] cli.main -> HermesCLI.run")
        print("Mini Hermes started. Type /quit to exit.\n")
        while True:
            user_input = input("You > ").strip()
            if not user_input:
                continue
            if user_input == "/quit":
                print("Bye.")
                return
            self.chat(user_input)

    def chat(self, message: str) -> str:
        print(f"[3] HermesCLI.chat received: {message!r}")
        result = self.agent.run_conversation(
            user_message=message,
            conversation_history=self.conversation_history,
        )
        self.conversation_history = result["messages"]
        response = result["final_response"]
        print(f"Hermes > {response}\n")
        return response


def main(
    *,
    model: str,
    base_url: str,
) -> None:
    cli = HermesCLI(model=model, base_url=base_url)
    cli.run()
