// src/services/websocket.js

let socket = null;

export const connectWebSocket = (onMessage) => {
  socket = new WebSocket("ws://localhost:8000/ws");

  socket.onopen = () => {
    console.log("WebSocket conectado");
  };

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);

    onMessage(data);
  };

  socket.onerror = (error) => {
    console.error("WebSocket Error:", error);
  };

  socket.onclose = () => {
    console.log("WebSocket cerrado");
  };
};

export const sendPatient = (patientData) => {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(patientData));
  }
};