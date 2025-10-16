import asyncio
import websockets
import json


async def chat_client():
    print("🔐 Secure Chat Client")
    server_url = input("Server URL (ws://localhost:8080): ") or "ws://localhost:8080"
    room_code = input("Room code: ")
    username = input("Your name: ")

    try:
        async with websockets.connect(server_url) as ws:
            await ws.send(json.dumps({'room_code': room_code, 'username': username}))
            print(f"✅ Connected to room '{room_code}' as '{username}'")

            async def listen():
                async for message in ws:
                    data = json.loads(message)
                    if data['type'] == 'message':
                        print(f"\n{data['username']}: {data['content']}")
                    elif data['type'] == 'user_joined':
                        print(f"\n⚡ {data['username']} joined")
                    elif data['type'] == 'user_left':
                        print(f"\n⚠️  {data['username']} left")
                    print("You: ", end="", flush=True)

            async def send():
                while True:
                    message = await asyncio.get_event_loop().run_in_executor(None, input, "You: ")
                    await ws.send(json.dumps({'content': message}))

            await asyncio.gather(listen(), send())

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(chat_client())