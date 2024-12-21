import asyncio
import websockets
from http.server import HTTPServer, BaseHTTPRequestHandler
import cgi
import threading

taskList = ['Task 1', 'Task 2', 'Task 3']
connected_clients = set()

class requestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.endswith('/tasklist'):
            self.send_response(200)
            self.send_header('content-type', 'text/html')
            self.end_headers()

            output = '<html><body>'
            output += '<h1>Task List</h1>'
            output += '<h3><a href="/tasklist/new">Add New Task</a></h3>'
            for task in taskList:
                output += task
                output += '<a href="/tasklist/%s/remove"> X</a><br>' % task
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/new'):
            self.send_response(200)
            self.send_header('content-type', 'text/html')
            self.end_headers()

            output = '<html><body>'
            output += '<h1>Add New Task</h1>'
            output += '<form method="POST" enctype="multipart/form-data" action="/tasklist/new">'
            output += '<input name="task" type="text" placeholder="Add new task">'
            output += '<input type="submit" value="Add"></form>'
            output += '</body></html>'
            self.wfile.write(output.encode())

        elif self.path.endswith('/remove'):
            task_to_remove = self.path.split('/')[2].replace('%20', ' ')
            self.send_response(200)
            self.send_header('content-type', 'text/html')
            self.end_headers()

            output = '<html><body>'
            output += f'<h1>Removed task: {task_to_remove}</h1>'
            output += f'<form method="POST" enctype="multipart/form-data" action="/tasklist/{task_to_remove}/remove">'
            output += '<input type="submit" value="Remove"></form>'
            output += '<a href="/tasklist">Cancel</a>'
            output += '</body></html>'
            self.wfile.write(output.encode())

    def do_POST(self):
        if self.path.endswith('/new'):
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
            content_len = int(self.headers.get('Content-length'))
            pdict['CONTENT-LENGTH'] = content_len
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                new_task = fields.get('task')[0]
                taskList.append(new_task)
                asyncio.run(broadcast_update(f"Task added: {new_task}"))

            self.send_response(301)
            self.send_header('content-type', 'text/html')
            self.send_header('Location', '/tasklist')
            self.end_headers()

        elif self.path.endswith('/remove'):
            task_to_remove = self.path.split('/')[2].replace('%20', ' ')
            if task_to_remove in taskList:
                taskList.remove(task_to_remove)
                asyncio.run(broadcast_update(f"Task removed: {task_to_remove}"))

            self.send_response(301)
            self.send_header('content-type', 'text/html')
            self.send_header('Location', '/tasklist')
            self.end_headers()

async def websocket_handler(websocket, path):
    print("WebSocket client connected.")
    connected_clients.add(websocket)
    try:
        while True:
            await websocket.recv()
    except websockets.ConnectionClosed:
        print("WebSocket client disconnected.")
    finally:
        connected_clients.remove(websocket)

async def broadcast_update(message):
    if connected_clients:
        await asyncio.wait([client.send(message) for client in connected_clients])

async def start_websocket_server():
    print("WebSocket server running on ws://localhost:8765")
    async with websockets.serve(websocket_handler, "localhost", 8765):
        await asyncio.Future()

def run_websocket_server():
    asyncio.run(start_websocket_server())

def main():
    PORT = 9000
    server_address = ('localhost', PORT)
    http_server = HTTPServer(server_address, requestHandler)
    print(f"HTTP Server running on port {PORT}")

    websocket_thread = threading.Thread(target=run_websocket_server, daemon=True)
    websocket_thread.start()

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down server.")

if __name__ == '__main__':
    main()
