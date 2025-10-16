import asyncio
import websockets
import json
import secrets
from datetime import datetime
import signal
import sys


class ChatServer:
    def __init__(self):
        self.active_rooms = {}
        self.user_connections = {}

    async def register_user(self, websocket, room_code, username):
        if room_code not in self.active_rooms:
            self.active_rooms[room_code] = {'users': set(), 'messages': []}

        self.active_rooms[room_code]['users'].add(username)
        self.user_connections[websocket] = {'username': username, 'room_code': room_code}

        join_message = {
            'type': 'user_joined',
            'username': username,
            'users_list': list(self.active_rooms[room_code]['users'])
        }
        await self.broadcast_to_room(room_code, join_message)
        return True

    async def handle_message(self, websocket, message_data):
        user_data = self.user_connections.get(websocket)
        if not user_data: return

        message_obj = {
            'type': 'message',
            'username': user_data['username'],
            'content': message_data['content'],
            'timestamp': datetime.now().isoformat()
        }

        room_code = user_data['room_code']
        self.active_rooms[room_code]['messages'].append(message_obj)
        await self.broadcast_to_room(room_code, message_obj)

    async def broadcast_to_room(self, room_code, message):
        disconnected = []
        for ws, user_data in self.user_connections.items():
            if user_data['room_code'] == room_code:
                try:
                    await ws.send(json.dumps(message))
                except:
                    disconnected.append(ws)
        for ws in disconnected: await self.handle_disconnect(ws)

    async def handle_disconnect(self, websocket):
        user_data = self.user_connections.get(websocket)
        if user_data:
            room_code = user_data['room_code']
            self.active_rooms[room_code]['users'].discard(user_data['username'])
            leave_message = {'type': 'user_left', 'username': user_data['username']}
            await self.broadcast_to_room(room_code, leave_message)
            if websocket in self.user_connections: del self.user_connections[websocket]

    async def handler(self, websocket, path):
        try:
            init_data = await websocket.recv()
            room_code = json.loads(init_data).get('room_code')
            username = json.loads(init_data).get('username', 'Anonymous')

            if not room_code: return

            await self.register_user(websocket, room_code, username)

            async for message in websocket:
                await self.handle_message(websocket, json.loads(message))

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await self.handle_disconnect(websocket)


async def main():
    server = ChatServer()
    port = 8080

    print(f"🚀 Server starting on port {port}")
    print("📡 URL: https://{codespace-id}-{port}.app.github.dev")

    async with websockets.serve(server.handler, "0.0.0.0", port):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())