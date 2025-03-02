import asyncio
import json
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from call_matcher import CallMatcher
from connection_manager import ConnectionManager

app = FastAPI()
manager = ConnectionManager()
matcher = CallMatcher()

SESSION_DURATION = 120  # 2 minutes in seconds


async def session_timer(user1: str, user2: str):
    """Ends a call after SESSION_DURATION seconds by sending a 'call_end' message to both clients."""
    await asyncio.sleep(SESSION_DURATION)
    end_message = json.dumps({"type": "call_end", "payload": {"reason": "timeout"}})
    await manager.send_personal_message(end_message, user1)
    await manager.send_personal_message(end_message, user2)
    matcher.remove_user(user1)
    matcher.remove_user(user2)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Generate a unique user_id for this connection.
    user_id = str(uuid.uuid4())
    await manager.connect(user_id, websocket)
    try:
        # Try to match this user immediately.
        match = matcher.add_user(user_id)
        if match is None:
            waiting_message = json.dumps({
                "type": "waiting",
                "payload": {"message": "Waiting for a partner..."}
            })
            await manager.send_personal_message(waiting_message, user_id)
        else:
            # A partner is available: retrieve both user IDs and session info.
            user1, user2 = match
            session_id = matcher.get_session(user_id)
            # Send a "matched" message to both users with the partner's ID.
            partner_id = user2 if user_id == user1 else user1
            matched_message_user1 = json.dumps({
                "type": "matched",
                "payload": {"session_id": session_id, "partner": user2, "initiator": True}
            })
            matched_message_user2 = json.dumps({
                "type": "matched",
                "payload": {"session_id": session_id, "partner": user1, "initiator": False}
            })
            await manager.send_personal_message(matched_message_user1, user1)
            await manager.send_personal_message(matched_message_user2, user2)
            # Start the session timer for auto termination after 2 minutes.
            asyncio.create_task(session_timer(user1, user2))

        # Main loop: process incoming messages from the client.
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            message_type = message.get("type")
            payload = message.get("payload")

            if message_type == "signal":
                # Relay signaling data (e.g., SDP, ICE candidates) to the partner.
                session_id = matcher.get_session(user_id)
                if session_id:
                    pair = matcher.active_sessions.get(session_id)
                    if pair:
                        partner_id = pair[0] if pair[1] == user_id else pair[1]
                        forward_message = json.dumps({"type": "signal", "payload": payload})
                        await manager.send_personal_message(forward_message, partner_id)
            elif message_type == "call_end":
                # When a user manually ends the call, notify the partner.
                session_id = matcher.get_session(user_id)
                if session_id:
                    pair = matcher.active_sessions.get(session_id)
                    if pair:
                        partner_id = pair[0] if pair[1] == user_id else pair[1]
                        end_message = json.dumps({
                            "type": "call_end",
                            "payload": {"reason": "manual_end"}
                        })
                        await manager.send_personal_message(end_message, partner_id)
                    matcher.remove_user(user_id)
            else:
                error_message = json.dumps({
                    "type": "error",
                    "payload": {"message": "Unknown message type"}
                })
                await manager.send_personal_message(error_message, user_id)

    except WebSocketDisconnect:
        matcher.remove_user(user_id)
        manager.disconnect(user_id)
    except Exception as e:
        error_message = json.dumps({
            "type": "error",
            "payload": {"message": str(e)}
        })
        await manager.send_personal_message(error_message, user_id)
        matcher.remove_user(user_id)
        manager.disconnect(user_id)
