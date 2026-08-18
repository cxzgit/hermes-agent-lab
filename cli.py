"""Interactive CLI: read input, call the Agent, and retain history."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from hermes_state import SessionDB
from run_agent import AIAgent


class HermesCLI:
    def __init__(
        self,
        *,
        model: str,
        base_url: str,
        client=None,
        db_path: Path | str | None = None,
        session_id: str | None = None,
    ) -> None:
        self._session_db = SessionDB(db_path)
        if session_id is None:
            self.session_id = uuid4().hex
            self._session_db.create_session(self.session_id, source="cli")
            self.conversation_history: list[dict] = []
        else:
            if not self._session_db.session_exists(session_id):
                self._session_db.close()
                raise ValueError(f"Session not found: {session_id}")
            self.session_id = session_id
            self.conversation_history = (
                self._session_db.get_messages_as_conversation(session_id)
            )

        # Reuse one Agent throughout this CLI session.
        self.agent = AIAgent(
            model=model,
            base_url=base_url,
            client=client,
            session_db=self._session_db,
            session_id=self.session_id,
        )

    def run(self) -> None:
        print("[2] cli.main -> HermesCLI.run")
        print(f"Session: {self.session_id}")
        if self.conversation_history:
            print(f"Restored {len(self.conversation_history)} message(s).")
        print("Mini Hermes started. Type /quit to exit.\n")
        try:
            while True:
                user_input = input("You > ").strip()
                if not user_input:
                    continue
                if user_input == "/quit":
                    print("Bye.")
                    return
                self.chat(user_input)
        finally:
            self.close()

    def close(self) -> None:
        self._session_db.close()

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
    session_id: str | None = None,
) -> None:
    cli = HermesCLI(model=model, base_url=base_url, session_id=session_id)
    cli.run()
