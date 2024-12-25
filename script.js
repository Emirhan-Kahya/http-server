/*
WebSocket Chat Uygulaması - Client
---------------------------------
Bu uygulama, WebSocket üzerinden gerçek zamanlı mesajlaşma sağlayan bir web istemcisidir.

Teknik Özellikler:
- WebSocket ile anlık mesajlaşma
- Oturum yönetimi (localStorage)
- Otomatik bağlantı yenileme
- Terminal logları
- Responsive tasarım
- Dosya ve resim paylaşımı desteği
*/

document.addEventListener('DOMContentLoaded', function() {
    // Durum değişkenleri - Uygulama durumunu saklar
    let ws = null;  // WebSocket bağlantısı
    let authToken = localStorage.getItem('authToken');  // Oturum token'ı
    
    // DOM elementleri - Performans için tek seferde tanımlama
    const elements = {
        status: document.getElementById('status'),  // Bağlantı durumu göstergesi
        messageContainer: document.getElementById('messageContainer'),  // Mesaj alanı
        messageForm: document.getElementById('messageForm'),  // Mesaj formu
        messageInput: document.getElementById('messageInput'),  // Mesaj girişi
        serverLogs: document.getElementById('serverLogs'),  // Terminal logları
        authContainer: document.getElementById('authContainer'),  // Giriş/kayıt formu
        chatContainer: document.getElementById('chatContainer'),  // Chat alanı
        chatUsername: document.getElementById('chatUsername')  // Kullanıcı adı göstergesi
    };

    // Sayfa yüklendiğinde token varsa otomatik giriş yap
    if (authToken) {
        showChat();
        connect();
    }

    // WebSocket Fonksiyonları
    function connect() {
        /*
        WebSocket bağlantısını kurar ve yönetir
        - Token kontrolü yapar
        - Varsa eski bağlantıyı kapatır
        - Yeni bağlantı açar
        - Bağlantı durumunu gösterir
        - Hata durumlarını yönetir
        */
        if (!authToken) return;
        
        if (ws) {
            ws.close();
            ws = null;
        }
        
        // WebSocket bağlantısını başlat
        ws = new WebSocket(`ws://${window.location.host}/ws?token=${authToken}`);
        
        // Bağlantı açıldığında
        ws.onopen = () => {
            elements.status.className = 'status-indicator connected';
            addServerLog('WebSocket bağlantısı kuruldu');
        };

        // Mesaj alındığında
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.type === 'system') {
                    addServerLog(data.message);
                    // Karşı tarafın kullanıcı adını güncelle
                    if (data.message.startsWith('Chatting with: ')) {
                        const otherUser = data.message.replace('Chatting with: ', '');
                        updateChatUsername(otherUser);
                    }
                } else if (data.type === 'message') {
                    addMessage(data.message, data.username);
                    // Mesaj logunu ekle
                    const currentUser = localStorage.getItem('username');
                    const direction = data.username === currentUser ? 'Sent to' : 'Received from';
                    addServerLog(`Message ${direction} ${data.username}: ${data.message}`);
                }
            } catch (error) {
                console.error('Message processing error:', error);
                addServerLog('Error processing message');
            }
        };

        // Bağlantı kapandığında
        ws.onclose = () => {
            elements.status.className = 'status-indicator disconnected';
            addServerLog('WebSocket bağlantısı kapandı');
            ws = null;
        };

        // Bağlantı hatası olduğunda
        ws.onerror = () => {
            addServerLog('Bağlantı hatası oluştu');
        };
    }

    // Mesaj İşleme Fonksiyonları
    function addMessage(message, username) {
        /*
        Mesajı chat alanına ekler
        - Mesaj balonunu oluşturur
        - Gönderen/alıcıya göre stil uygular
        - Zaman bilgisi ekler
        - Otomatik kaydırma yapar
        */
        const messageWrapper = document.createElement('div');
        const messageDiv = document.createElement('div');
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        // Mesaj balonu oluştur
        messageDiv.className = `message ${username === localStorage.getItem('username') ? 'sent' : 'received'}`;
        messageDiv.innerHTML = `
            <div class="message-content">${message}</div>
            <div class="message-info">
                <span class="message-time">${time}</span>
            </div>
        `;
        
        messageWrapper.appendChild(messageDiv);
        messageWrapper.appendChild(document.createElement('div')).className = 'clearfix';
        
        elements.messageContainer.appendChild(messageWrapper);
        elements.messageContainer.scrollTop = elements.messageContainer.scrollHeight;
    }

    function addServerLog(message) {
        /*
        Terminal loglarını ekler
        - Zaman damgası ekler
        - Thread bilgisini özel formatta gösterir
        - Otomatik kaydırma yapar
        */
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        
        // Thread bilgisi içeren mesajları özel formatta göster
        if (message.includes('Thread #') || message.includes('Channel')) {
            const [action, threadInfo] = message.split(' - ');
            logEntry.innerHTML = `${time} ${action} - <span class="thread-info">${threadInfo}</span>`;
        } else {
            logEntry.innerHTML = `${time} ${message}`;
        }
        
        elements.serverLogs.appendChild(logEntry);
        elements.serverLogs.scrollTop = elements.serverLogs.scrollHeight;
    }

    // Kullanıcı İşlemleri
    async function login() {
        /*
        Kullanıcı girişi yapar
        - Form verilerini alır
        - API'ye gönderir
        - Token'ı saklar
        - Chat ekranını gösterir
        - WebSocket bağlantısı kurar
        */
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;

        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (response.ok) {
                const data = await response.json();
                authToken = data.token;
                localStorage.setItem('authToken', authToken);
                localStorage.setItem('username', username);
                showChat();
                updateChatUsername(username);
                connect();
            } else {
                alert(await response.text());
            }
        } catch (error) {
            alert('Login failed: ' + error.message);
        }
    }

    async function register() {
        /*
        Yeni kullanıcı kaydı yapar
        - Form verilerini alır
        - API'ye gönderir
        - Başarılı kayıt sonrası giriş formunu gösterir
        */
        const username = document.getElementById('registerUsername').value;
        const password = document.getElementById('registerPassword').value;

        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            if (response.ok) {
                alert('Registration successful! Please login.');
                toggleAuth();
            } else {
                alert(await response.text());
            }
        } catch (error) {
            alert('Registration failed: ' + error.message);
        }
    }

    function logout() {
        /*
        Kullanıcı çıkışı yapar
        - WebSocket bağlantısını kapatır
        - Token'ı temizler
        - Giriş ekranına döner
        */
        if (ws) ws.close();
        authToken = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('username');
        showAuth();
    }

    // Arayüz Fonksiyonları
    function showAuth() {
        /*
        Giriş/kayıt formunu gösterir
        - Chat alanını gizler
        - Auth formunu gösterir
        */
        elements.authContainer.style.display = 'flex';
        elements.chatContainer.style.display = 'none';
    }

    function showChat() {
        /*
        Chat arayüzünü gösterir
        - Auth formunu gizler
        - Chat alanını gösterir
        - Kullanıcı adını günceller
        */
        elements.authContainer.style.display = 'none';
        elements.chatContainer.style.display = 'flex';
        const username = localStorage.getItem('username');
        if (username) updateChatUsername(username);
    }

    function toggleAuth() {
        /*
        Giriş ve kayıt formları arasında geçiş yapar
        - Mevcut formu gizler
        - Diğer formu gösterir
        */
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');
        loginForm.style.display = loginForm.style.display === 'none' ? 'block' : 'none';
        registerForm.style.display = registerForm.style.display === 'none' ? 'block' : 'none';
    }

    function updateChatUsername(username) {
        /*
        Chat başlığındaki kullanıcı adını günceller
        */
        elements.chatUsername.textContent = username;
    }

    // Olay Dinleyicileri
    elements.messageForm.addEventListener('submit', async function(e) {
        /*
        Mesaj gönderme formunu yönetir
        - Form submit olayını yakalar
        - Mesajı alır ve kontrol eder
        - WebSocket bağlantısını kontrol eder
        - Mesajı gönderir
        - Hata durumlarını yönetir
        */
        e.preventDefault();
        const message = elements.messageInput.value.trim();
        
        if (!message) return;
        
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            addServerLog('Bağlantı kuruluyor...');
            connect();
            return;
        }
        
        try {
            ws.send(message);
            elements.messageInput.value = '';
        } catch (error) {
            console.error('Send error:', error);
            addServerLog('Mesaj gönderilirken hata oluştu');
            connect();
        }
    });

    // HTML için global fonksiyonlar
    window.login = login;
    window.register = register;
    window.logout = logout;
    window.toggleAuth = toggleAuth;
});