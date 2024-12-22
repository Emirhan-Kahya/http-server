import asyncio
from aiohttp import web
import json
import pathlib
import threading
from concurrent.futures import ThreadPoolExecutor

# Global değişken
connected_clients = set()

# Global thread pool
executor = ThreadPoolExecutor(max_workers=4)

async def index_handler(request):
    return web.FileResponse('index.html')

async def style_handler(request):
    return web.FileResponse('style.css')

async def script_handler(request):
    return web.FileResponse('script.js')

async def websocket_handler(request):
    ws = web.WebSocketResponse(autoping=True)
    await ws.prepare(request)
    
    print(f"WebSocket connection ready on thread: {threading.current_thread().name}")
    connected_clients.add(ws)
    
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                # Ağır işlemleri thread pool'da çalıştır
                def process_message(message):
                    print(f"Processing message on thread: {threading.current_thread().name}")
                    return message

                result = await asyncio.get_running_loop().run_in_executor(
                    executor, 
                    process_message, 
                    msg.data
                )
                
                for client in connected_clients:
                    await client.send_str(result)
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
