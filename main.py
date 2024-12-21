import asyncio
import websockets
from http.server import SimpleHTTPRequestHandler, HTTPServer
import threading

# HTTP Server for Serving index.html
HOST = 'localhost'
HTTP_PORT = 8080
WS_PORT = 8765

# HTTP Server Configuration
class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = 'index.html'
        return super().do_GET()

def run_http_server():
    server_address = (HOST, HTTP_PORT)
    httpd = HTTPServer(server_address, CustomHTTPRequestHandler)
    print(f"HTTP Server running at http://{HOST}:{HTTP_PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down HTTP server.")
        httpd.server_close()

# WebSocket Server
async def websocket_handler(websocket, path):
    print(f"WebSocket connection established at path: {path}")
    try:
        async for message in websocket:
            print(f"Received message: {message}")
            response = f"Server received: {message}"
            await websocket.send(response)
    except websockets.ConnectionClosed as e:
        print(f"WebSocket connection closed at path: {path} ({e})")

def run_websocket_server():
    async def start_server():
        print(f"WebSocket Server running at ws://{HOST}:{WS_PORT}")
        server = await websockets.serve(websocket_handler, HOST, WS_PORT)
        await server.wait_closed()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_server())
    except KeyboardInterrupt:
        print("\nShutting down WebSocket server.")
    finally:
        loop.close()

# Main Execution
if __name__ == '__main__':
    # Start HTTP server in a thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    # Start WebSocket server in a thread
    websocket_thread = threading.Thread(target=run_websocket_server, daemon=True)
    websocket_thread.start()

    # Keep main thread alive
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nShutting down servers.")
