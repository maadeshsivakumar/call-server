import json

from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_matching_and_signaling():
    with client.websocket_connect("/ws") as ws1, client.websocket_connect("/ws") as ws2:
        # Wait for both to be matched.
        msg1 = json.loads(ws1.receive_text())
        if msg1["type"] == "waiting":
            msg1 = json.loads(ws1.receive_text())
        msg2 = json.loads(ws2.receive_text())
        if msg2["type"] == "waiting":
            msg2 = json.loads(ws2.receive_text())
        assert msg1["type"] == "matched"
        assert msg2["type"] == "matched"

        # Now, simulate a signaling message from ws1 to be relayed to ws2.
        signal_payload = {"sdp": "dummy_sdp", "ice": "dummy_ice_candidate"}
        ws1.send_text(json.dumps({"type": "signal", "payload": signal_payload}))
        received = json.loads(ws2.receive_text())
        assert received["type"] == "signal"
        assert received["payload"] == signal_payload


def test_unknown_message_type():
    with client.websocket_connect("/ws") as ws:
        # Receive initial waiting or matched message (ignored for this test).
        msg = json.loads(ws.receive_text())
        # Send an unknown message.
        ws.send_text(json.dumps({"type": "unknown", "payload": {}}))
        error_msg = json.loads(ws.receive_text())
        assert error_msg["type"] == "error"
        assert "Unknown message type" in error_msg["payload"]["message"]


def test_manual_call_end():
    with client.websocket_connect("/ws") as ws1, client.websocket_connect("/ws") as ws2:
        # Wait for both to be matched.
        msg1 = json.loads(ws1.receive_text())
        if msg1["type"] == "waiting":
            msg1 = json.loads(ws1.receive_text())
        msg2 = json.loads(ws2.receive_text())
        if msg2["type"] == "waiting":
            msg2 = json.loads(ws2.receive_text())
        assert msg1["type"] == "matched"
        assert msg2["type"] == "matched"

        # Send manual call_end from ws1.
        ws1.send_text(json.dumps({"type": "call_end", "payload": {}}))
        # ws2 should receive a call_end message with reason "manual_end".
        end_msg = json.loads(ws2.receive_text())
        assert end_msg["type"] == "call_end"
        assert end_msg["payload"]["reason"] == "manual_end"