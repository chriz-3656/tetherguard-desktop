import asyncio
import websockets
import json

connected_clients = set()

async def handler(websocket):
    print("New client connected.")
    connected_clients.add(websocket)
    try:
        async for message in websocket:
            print(f"Received message: {message[:100]}...") # Print first 100 chars
            
            # Broadcast to all other connected clients (useful for the demo phone UI)
            for client in connected_clients:
                if client != websocket:
                    try:
                        await client.send(message)
                    except websockets.exceptions.ConnectionClosed:
                        pass
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected.")
    finally:
        connected_clients.remove(websocket)

async def main():
    print("Starting WebSocket Relay Server on ws://localhost:8080")
    async with websockets.serve(handler, "localhost", 8080):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
