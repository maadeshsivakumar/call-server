from fastapi import FastAPI, WebSocket
from connection_manager import ConnectionManager

app = FastAPI()
manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    A simple WebSocket endpoint that accepts a connection,
    echoes back received messages, and disconnects on error.
    """
    user_id = "dummy_user"  # In later commits, this will be generated dynamically
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You said: {data}", user_id)
    except Exception:
        manager.disconnect(user_id)
