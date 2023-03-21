const WebSocket = require('ws');

const server = new WebSocket.Server({ port: 5000 });

server.on('connection', (socket) => {
  console.log('Cliente conectado');

  socket.on('message', (message) => {
    console.log(`Mensaje recibido: ${message}`);

    // Aquí puedes agregar la lógica para procesar el mensaje recibido y enviar una respuesta al cliente
    socket.send('Mensaje recibido');
  });

  socket.on('close', () => {
    console.log('Cliente desconectado');
  });
});
