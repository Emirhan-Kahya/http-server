from http.server import SimpleHTTPRequestHandler, HTTPServer
import asyncio
import websockets
import threading
import os

# Sunucunun calisacagi adres ve port bilgileri
HOST = 'localhost'
HTTP_PORT = 8080
WS_PORT = 8765

# Web sitesi dosyalarının bulundugu dizin
WEBSITE_DIR = "."

# Cok is parcaciklı (multithreaded) HTTP Sunucusu
class ThreadedHTTPServer(HTTPServer):
    """Her HTTP isteğini ayrı bir iş parçacığında işleyen HTTP Sunucusu."""
    def process_request(self, request, client_address):
        # İsteği ayri bir iş parçaciğinda isler
        threading.Thread(target=self.__handle_request, args=(request, client_address)).start()

    def __handle_request(self, request, client_address):
        # İstegi tamamlar ve baglantiyi kapatir
        self.finish_request(request, client_address)
        self.shutdown_request(request)

# WebSocket Sunucusunu çalıstırmak icin is parçacigi
class WebSocketServerThread(threading.Thread):
    def run(self):
        # WebSocket baglantilarini yoneten islev
        async def websocket_handler(websocket, path):
            print("Yeni bir WebSocket bağlantısı kuruldu.")
            connected_clients.add(websocket)
            try:
                # Gelen mesajlari al ve diger istemcilere ilet
                async for message in websocket:
                    print(f"Gelen mesaj: {message}")
                    # Mesajı diğer tum baglı istemcilere ilet
                    for client in connected_clients:
                        if client != websocket:  # Gönderen istemciye geri göndermemek için
                            await client.send(f"Sunucu: {message}")
            except websockets.exceptions.ConnectionClosed:
                print("WebSocket bağlantısı kapatıldı.")
            finally:
                # İstemci baglantisini kaldirir
                connected_clients.remove(websocket)

        # WebSocket sunucusunu baslatan islev
        async def start_websocket_server():
            print(f"WebSocket Sunucusu ws://{HOST}:{WS_PORT} adresinde çalışıyor.")
            async with websockets.serve(websocket_handler, HOST, WS_PORT):
                await asyncio.Future()  # Sonsuza kadar çalıştırir

        # Bagli istemciler için bir küme (set)
        connected_clients = set()
        # WebSocket sunucusunu başlatir
        asyncio.run(start_websocket_server())

# main 
if __name__ == "__main__":
    # Web sitesi dizinini
    os.chdir(WEBSITE_DIR)

    # HTTP sunucusunu bir iş parçacığında başlatiyor
    http_server = ThreadedHTTPServer((HOST, HTTP_PORT), SimpleHTTPRequestHandler)
    http_thread = threading.Thread(target=http_server.serve_forever)
    http_thread.daemon = True
    http_thread.start()
    print(f"HTTP Sunucusu http://{HOST}:{HTTP_PORT} adresinde çalışıyor.")

    # WebSocket sunucusunu bir iş parçaciginda baslatir
    ws_thread = WebSocketServerThread()
    ws_thread.daemon = True
    ws_thread.start()

    # Ana iş parçaciğini canli tutar
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nSunucular kapatılıyor...")
        http_server.shutdown()
