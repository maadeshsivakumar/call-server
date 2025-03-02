import pytest

from connection_manager import ConnectionManager


# A dummy WebSocket implementation for testing purposes.
class DummyWebSocket:
    def __init__(self):
        self.accepted = False
        self.sent_messages = []

    async def accept(self):
        self.accepted = True

    async def send_text(self, message: str):
        self.sent_messages.append(message)


@pytest.mark.asyncio
async def test_connect_and_send_personal_message():
    manager = ConnectionManager()
    dummy_ws = DummyWebSocket()
    user_id = "user1"

    await manager.connect(user_id, dummy_ws)
    assert dummy_ws.accepted is True

    test_message = "Hello, user1!"
    await manager.send_personal_message(test_message, user_id)
    assert test_message in dummy_ws.sent_messages


@pytest.mark.asyncio
async def test_disconnect():
    manager = ConnectionManager()
    dummy_ws = DummyWebSocket()
    user_id = "user1"

    await manager.connect(user_id, dummy_ws)
    manager.disconnect(user_id)
    assert user_id not in manager.active_connections


@pytest.mark.asyncio
async def test_broadcast():
    manager = ConnectionManager()
    dummy_ws1 = DummyWebSocket()
    dummy_ws2 = DummyWebSocket()

    await manager.connect("user1", dummy_ws1)
    await manager.connect("user2", dummy_ws2)

    test_message = "Broadcast message"
    await manager.broadcast(test_message)
    assert test_message in dummy_ws1.sent_messages
    assert test_message in dummy_ws2.sent_messages
