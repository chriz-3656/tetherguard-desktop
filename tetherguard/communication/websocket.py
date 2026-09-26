import asyncio
import json
import websockets
from typing import Callable, Optional, Dict, Any
from threading import Thread

class RelayClient:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.ws = None
        self.is_connected = False
        self._loop = None
        self._thread = None
        self.on_command: Callable[[Dict[str, Any]], None] = None
        self._stop_event = asyncio.Event()

    def start(self):
        self._thread = Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        if self._loop:
            self._loop.call_soon_threadsafe(self._stop_event.set)
        if self._thread:
            self._thread.join(timeout=2)

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connect_and_listen())

    async def _connect_and_listen(self):
        while not self._stop_event.is_set():
            try:
                async with websockets.connect(self.endpoint) as ws:
                    self.ws = ws
                    self.is_connected = True
                    print(f"Connected to relay: {self.endpoint}")
                    
                    while not self._stop_event.is_set():
                        try:
                            # Wait for message or stop event
                            msg_task = asyncio.create_task(ws.recv())
                            stop_task = asyncio.create_task(self._stop_event.wait())
                            
                            done, pending = await asyncio.wait(
                                [msg_task, stop_task],
                                return_when=asyncio.FIRST_COMPLETED
                            )
                            
                            if stop_task in done:
                                msg_task.cancel()
                                break
                                
                            message = msg_task.result()
                            if self.on_command:
                                try:
                                    data = json.loads(message)
                                    self.on_command(data)
                                except json.JSONDecodeError:
                                    print("Received invalid JSON from relay.")
                                    
                        except websockets.exceptions.ConnectionClosed:
                            print("Connection closed by server.")
                            break
            except Exception as e:
                print(f"WebSocket connection error: {e}")
                self.is_connected = False
                
            if not self._stop_event.is_set():
                await asyncio.sleep(5) # Reconnect delay
                
        self.is_connected = False

    def send_message(self, message: Dict[str, Any]):
        if self.ws and self.is_connected and self._loop:
            payload = json.dumps(message)
            asyncio.run_coroutine_threadsafe(self.ws.send(payload), self._loop)
