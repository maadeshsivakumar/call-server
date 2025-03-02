from typing import Optional, Tuple, List, Dict


class CallMatcher:
    def __init__(self):
        self.waiting_queue: List[str] = []
        self.active_sessions: Dict[str, Tuple[str, str]] = {}
        self.user_session_map: Dict[str, str] = {}

    def add_user(self, user_id: str) -> Optional[Tuple[str, str]]:
        """
        Adds a user to the waiting queue. If there's already a waiting user,
        matches them and returns a tuple of the paired user IDs.
        Otherwise, returns None.
        """
        if self.waiting_queue:
            partner_id = self.waiting_queue.pop(0)
            session_id = f"session_{partner_id}_{user_id}"
            self.active_sessions[session_id] = (partner_id, user_id)
            self.user_session_map[partner_id] = session_id
            self.user_session_map[user_id] = session_id
            return partner_id, user_id
        else:
            self.waiting_queue.append(user_id)
            return None

    def remove_user(self, user_id: str) -> None:
        """
        Removes a user from the waiting queue or an active session.
        If the user is in an active session, the session is removed entirely.
        """
        if user_id in self.waiting_queue:
            self.waiting_queue.remove(user_id)
        if user_id in self.user_session_map:
            session_id = self.user_session_map[user_id]
            if session_id in self.active_sessions:
                # Remove the session for both users.
                pair = self.active_sessions.pop(session_id)
                for uid in pair:
                    if uid in self.user_session_map:
                        del self.user_session_map[uid]

    def get_session(self, user_id: str) -> Optional[str]:
        """
        Returns the session ID for the given user if they are in an active session.
        """
        return self.user_session_map.get(user_id)
