from call_matcher import CallMatcher


def test_add_user_no_partner():
    matcher = CallMatcher()
    result = matcher.add_user("user1")
    assert result is None
    # The user should be in the waiting queue.
    assert "user1" in matcher.waiting_queue


def test_add_user_with_partner():
    matcher = CallMatcher()
    # First user is added and waits.
    matcher.add_user("user1")
    # Second user gets paired with the waiting user.
    result = matcher.add_user("user2")
    assert result is not None
    # Our implementation returns (waiting_user, new_user).
    assert result == ("user1", "user2")
    session_id = matcher.get_session("user1")
    assert session_id is not None
    # Both users should map to the same session.
    assert matcher.get_session("user2") == session_id
    assert session_id in matcher.active_sessions


def test_remove_user_from_waiting():
    matcher = CallMatcher()
    matcher.add_user("user1")
    matcher.remove_user("user1")
    assert "user1" not in matcher.waiting_queue


def test_remove_user_from_session():
    matcher = CallMatcher()
    matcher.add_user("user1")
    matcher.add_user("user2")
    session_id = matcher.get_session("user1")
    assert session_id is not None
    matcher.remove_user("user1")
    # After removal, neither user should be in an active session.
    assert matcher.get_session("user1") is None
    assert matcher.get_session("user2") is None
    assert session_id not in matcher.active_sessions
