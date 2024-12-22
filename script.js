document.addEventListener('DOMContentLoaded', function() {
    let ws = null;
    const statusDiv = document.getElementById('status');
    const messageContainer = document.getElementById('messageContainer');
    const messageForm = document.getElementById('messageForm');
    const messageInput = document.getElementById('messageInput');
    const serverLogs = document.getElementById('serverLogs');

    function connect() {
        ws = new WebSocket(`ws://${window.location.host}/ws`);

        ws.onopen = function() {
            statusDiv.className = 'status-indicator connected';
            addServerLog('WebSocket connection established');
        };

        ws.onmessage = function(event) {
            addServerLog(`Message received: ${event.data}`);
        };

        ws.onclose = function() {
            statusDiv.className = 'status-indicator disconnected';
            addServerLog('WebSocket connection closed');
            setTimeout(connect, 3000);
        };

        ws.onerror = function(error) {
            addServerLog(`Error: ${error.message}`);
        };
    }

    function addMessage(message) {
        const messageWrapper = document.createElement('div');
        const messageDiv = document.createElement('div');
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.className = 'message sent';
        messageDiv.innerHTML = `
            <div class="message-content">${message}</div>
            <span class="message-time">${time}</span>
        `;
        
        messageWrapper.appendChild(messageDiv);
        
        const clearfix = document.createElement('div');
        clearfix.className = 'clearfix';
        messageWrapper.appendChild(clearfix);
        
        messageContainer.appendChild(messageWrapper);
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }

    function addServerLog(message) {
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        logEntry.innerHTML = `<span class="log-time">[${time}]</span> ${message}`;
        serverLogs.appendChild(logEntry);
        serverLogs.scrollTop = serverLogs.scrollHeight;
    }

    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        if (ws && messageInput.value) {
            const message = messageInput.value;
            ws.send(message);
            addMessage(message);
            addServerLog(`Message sent: ${message}`);
            messageInput.value = '';
        }
    });

    connect();
});