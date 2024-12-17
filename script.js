const ws = new WebSocket("ws://localhost:8765");

// WebSocketi dinler
ws.onopen = () => {
    console.log("WebSocket connection established");
    document.getElementById("messages").innerHTML += `<p><strong>Connected to WebSocket server</strong></p>`;
};

ws.onmessage = (event) => {
    console.log("Message received from server:", event.data);
    document.getElementById("messages").innerHTML += `<p>${event.data}</p>`;
};

ws.onclose = () => {
    console.log("WebSocket connection closed");
    document.getElementById("messages").innerHTML += `<p><strong>Disconnected from WebSocket server</strong></p>`;
};

// WebSocket'e mesaji iletir
document.getElementById("sendMessage").addEventListener("click", () => {
    const message = document.getElementById("messageInput").value;
    if (message) {
        ws.send(message);
        document.getElementById("messages").innerHTML += `<p><strong>You:</strong> ${message}</p>`;
        document.getElementById("messageInput").value = "";
    }
});
