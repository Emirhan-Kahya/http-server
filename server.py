import asyncio
from aiohttp import web
import json
import pathlib

# Global değişken
connected_clients = set()

async def index_handler(request):
    return web.FileResponse('index.html')

async def style_handler(request):
    return web.FileResponse('style.css')

async def script_handler(request):
    return web.FileResponse('script.js')

async def websocket_handler(request):
    ws = web.WebSocketResponse(autoping=True)
    await ws.prepare(request)
    
    print("WebSocket connection ready")
    connected_clients.add(ws)
    
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                print(f"Received message: {msg.data}")
                for client in connected_clients:
                    await client.send_str(msg.data)
            elif msg.type == web.WSMsgType.ERROR:
                print(f"WebSocket error: {ws.exception()}")
    finally:
        connected_clients.remove(ws)
    
    print("WebSocket connection closed")
    return ws

async def init_app():
    app = web.Application()
    
    # Her dosya için özel route
    app.router.add_get('/', index_handler)
    app.router.add_get('/style.css', style_handler)
    app.router.add_get('/script.js', script_handler)
    app.router.add_get('/ws', websocket_handler)
    
    return app

if __name__ == '__main__':
    app = asyncio.run(init_app())
    web.run_app(app, host='localhost', port=8080)
