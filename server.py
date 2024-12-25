"""
WebSocket Chat Uygulaması - Server
---------------------------------
Bu uygulama, gerçek zamanlı mesajlaşma imkanı sunan bir WebSocket sunucusudur.

Teknik Özellikler:
- WebSocket protokolü ile anlık mesajlaşma
- Çoklu thread kullanımı ile eşzamanlı işlem yapabilme
- Asenkron programlama (asyncio) ile yüksek performans
- Güvenli oturum yönetimi ve kullanıcı doğrulama
- Terminal logları ile işlem takibi
"""

import asyncio  # Asenkron işlemler için
from aiohttp import web  # Web sunucusu ve WebSocket desteği
import json  # JSON veri işleme
import pathlib  # Dosya yolu işlemleri
import threading  # Thread yönetimi
from concurrent.futures import ThreadPoolExecutor  # Çoklu thread havuzu
import secrets  # Güvenli token oluşturma
import random  # Rastgele sayı üretimi

# Global değişkenler - Uygulama durumunu saklar
connected_clients = {}  # Aktif WebSocket bağlantılarını saklar {websocket: {'username': 'user'}}
users = {}  # Kayıtlı kullanıcıları saklar {username: 'password'}
active_sessions = {}  # Aktif oturumları saklar {token: 'username'}

# Thread havuzu - Eşzamanlı işlemler için 4 worker thread
executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="Thread")

def get_thread_info():
    """
    Mevcut thread'in bilgisini döndürür.
    - Thread-0, Thread-1 gibi worker thread'ler için thread adını döndürür
    - Ana thread için "Main Channel" döndürür
    - Thread bilgisi loglama ve debugging için kullanılır
    """
    thread = threading.current_thread()
    return thread.name if thread.name.startswith('Thread') else "Main Channel"

async def send_system_message(ws, message):
    """
    Sistem mesajlarını gönderir.
    - Bağlantı durumu, hata mesajları gibi sistem bilgilerini kullanıcıya iletir
    - JSON formatında 'system' tipinde mesaj gönderir
    - WebSocket bağlantısı üzerinden asenkron olarak iletilir
    """
    await ws.send_str(json.dumps({'type': 'system', 'message': message}))

async def broadcast_message(message_data):
    """
    Mesajı tüm bağlı kullanıcılara iletir.
    - Gelen mesajı bağlı tüm kullanıcılara dağıtır
    - Bağlantısı kopan kullanıcıları listeden temizler
    - Her kullanıcı için asenkron olarak mesaj gönderir
    - Hata durumunda bağlantıyı temizler
    """
    for client in list(connected_clients.keys()):
        try:
            if not client.closed:
                await client.send_str(json.dumps(message_data))
        except:
            if client in connected_clients:
                del connected_clients[client]

async def process_in_background(message, username, ws):
    """
    Mesajları arka planda işler ve thread bilgisini loglar.
    - Mesajı thread havuzunda işlenmek üzere gönderir
    - İşlem sonucunu terminal loglarına ekler
    - CPU yoğun işlemleri ana thread'i bloklamadan yapar
    - İşlem tamamlandığında kullanıcıya bilgi verir
    """
    try:
        thread_info = await asyncio.get_running_loop().run_in_executor(
            executor,
            lambda: process_heavy_task(message, username)
        )
        if not ws.closed:
            await send_system_message(ws, f"Message processed - {thread_info}")
    except Exception as e:
        print(f"Background processing error: {e}")

def process_heavy_task(message, username):
    """
    CPU yoğun işlem simulasyonu yapar.
    - Thread kullanımını göstermek için yapay bir iş yükü oluşturur
    - Farklı thread'lerin paralel çalışmasını gösterir
    - İşlem süresi rastgele belirlenir (10-20M iterasyon)
    - Thread bilgisini döndürür
    """
    thread_info = get_thread_info()
    print(f"[{thread_info}] Processing message from {username}")
    
    # CPU yoğun işlem simulasyonu
    result = 0
    for i in range(random.randint(10_000_000, 20_000_000)):
        result += i
    
    print(f"[{thread_info}] Processing completed")
    return thread_info

# Kullanıcı işlemleri
async def register_handler(request):
    """
    Yeni kullanıcı kaydı oluşturur.
    - Kullanıcı adı ve şifre kontrolü yapar
    - Şifreyi düz metin olarak saklar
    - Başarılı/başarısız durumu bildirir
    - Aynı kullanıcı adıyla kayıt yapılmasını engeller
    """
    data = await request.json()
    username, password = data.get('username'), data.get('password')
    
    if not username or not password:
        return web.Response(status=400, text='Username and password required')
    if username in users:
        return web.Response(status=400, text='Username already exists')
    
    users[username] = password
    return web.Response(text='Registration successful')

async def login_handler(request):
    """
    Kullanıcı girişi yapar ve oturum token'ı oluşturur.
    - Kullanıcı bilgilerini doğrular
    - Önceki oturumları temizler
    - Yeni bir oturum token'ı oluşturur
    - Token'ı JSON formatında döndürür
    """
    data = await request.json()
    username, password = data.get('username'), data.get('password')
    
    if not username or not password:
        return web.Response(status=400, text='Username and password required')
    
    if username not in users or users[username] != password:
        return web.Response(status=401, text='Invalid credentials')
    
    # Önceki oturumları temizle
    for token, user in list(active_sessions.items()):
        if user == username:
            del active_sessions[token]
    
    token = secrets.token_urlsafe(32)
    active_sessions[token] = username
    return web.json_response({'token': token})

# WebSocket işleyici
async def websocket_handler(request):
    """
    WebSocket bağlantılarını yönetir ve mesajlaşmayı sağlar.
    - Token kontrolü ile güvenliği sağlar
    - Kullanıcı bağlantılarını yönetir
    - Mesajları anlık iletir ve işler
    - Kullanıcı durumlarını (aktif/pasif) yönetir
    - Bağlantı koptuğunda temizlik yapar
    - Diğer kullanıcılara durum bilgisi verir
    """
    ws = web.WebSocketResponse(autoping=True, heartbeat=30)
    await ws.prepare(request)
    
    # Token kontrolü
    token = request.query.get('token')
    if not token or token not in active_sessions:
        await ws.close(code=4001, message=b'Unauthorized')
        return ws
    
    username = active_sessions[token]
    thread_info = get_thread_info()
    
    # Aynı kullanıcının önceki bağlantılarını kapat
    for client in list(connected_clients.keys()):
        if connected_clients[client]['username'] == username:
            await client.close()
            del connected_clients[client]
    
    connected_clients[ws] = {'username': username}
    
    try:
        await send_system_message(ws, f"Connected - {thread_info}")
        
        # Aktif kullanıcı bilgisini gönder
        other_users = [info['username'] for client, info in connected_clients.items() 
                      if info['username'] != username and not client.closed]
        
        if other_users:
            # Diğer kullanıcı varsa onun ismini göster
            await send_system_message(ws, f"Chatting with: {other_users[0]}")
            # Diğer kullanıcıya da bilgi ver
            for client in connected_clients:
                if (connected_clients[client]['username'] in other_users and 
                    not client.closed):
                    await send_system_message(client, f"Chatting with: {username}")
        else:
            # Başka kullanıcı yoksa "No user active" göster
            await send_system_message(ws, "Chatting with: No user active")
        
        # Mesaj döngüsü
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    # Mesajı hemen gönder
                    await broadcast_message({
                        'type': 'message',
                        'username': username,
                        'message': msg.data,
                        'processed_by': thread_info
                    })
                    
                    # Arka planda işle
                    asyncio.create_task(process_in_background(msg.data, username, ws))
                except Exception as e:
                    print(f"Message error: {e}")
                    if not ws.closed:
                        await send_system_message(ws, "Error processing message")
            
            elif msg.type == web.WSMsgType.ERROR:
                print(f"WebSocket error: {ws.exception()}")
    except Exception as e:
        print(f"WebSocket handler error: {e}")
    finally:
        if ws in connected_clients:
            # Diğer kullanıcıya çıkış bilgisi gönder
            other_users = [info['username'] for client, info in connected_clients.items() 
                         if info['username'] != username and not client.closed]
            if other_users:
                for client in connected_clients:
                    if (connected_clients[client]['username'] in other_users and 
                        not client.closed):
                        await send_system_message(client, f"{username} disconnected")
                        await send_system_message(client, "Chatting with: No user active")
            del connected_clients[ws]
    
    return ws

# Statik dosya işleyicileri
async def index_handler(request): 
    """Ana sayfa HTML dosyasını gönderir"""
    return web.FileResponse('index.html')

async def style_handler(request): 
    """CSS stil dosyasını gönderir"""
    return web.FileResponse('style.css')

async def script_handler(request): 
    """JavaScript dosyasını gönderir"""
    return web.FileResponse('script.js')

# Uygulama başlatma
async def init_app():
    """
    Web uygulamasını başlatır ve rotaları ayarlar
    - Statik dosya rotaları
    - WebSocket rotası
    - API rotaları (login/register)
    """
    app = web.Application()
    
    # Rotalar
    app.router.add_get('/', index_handler)
    app.router.add_get('/style.css', style_handler)
    app.router.add_get('/script.js', script_handler)
    app.router.add_get('/ws', websocket_handler)
    app.router.add_post('/register', register_handler)
    app.router.add_post('/login', login_handler)
    
    print(f"[{get_thread_info()}] Server starting")
    return app

if __name__ == '__main__':
    app = asyncio.run(init_app())
    web.run_app(app, host='localhost', port=8080)
