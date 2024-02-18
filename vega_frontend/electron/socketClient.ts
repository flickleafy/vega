import { mainWindow } from './index';
import * as net from 'net';
import * as os from 'os';

const PORT = 9090;
const HOST = os.hostname();
const RECONNECT_INTERVAL = 5000;
const HEART_BEAT_INTERVAL = 3000;

let client: net.Socket;

export function connectToServer() {
  console.log('Connecting to server');

  client = new net.Socket();

  client.connect(PORT, HOST, () => {
    console.log(`Connected to server on ${HOST}:${PORT}`);
    sendDataPeriodically();
  });

  client.on('data', (data) => {
    console.log('Received: ' + data.toString());
    if (mainWindow) {
      mainWindow.webContents.send('data', JSON.parse(data.toString()));
    }
  });

  client.on('close', () => {
    console.log('Connection closed');
    attemptReconnect();
  });

  client.on('error', (err) => {
    console.error('Connection error: ' + err.message);
    client.destroy(); // Ensure the socket is closed before attempting to reconnect
    attemptReconnect();
  });
}

function attemptReconnect() {
  setTimeout(() => {
    console.log(`Attempting to reconnect...`);
    connectToServer();
  }, RECONNECT_INTERVAL);
}

export function sendDataPeriodically() {
  setInterval(() => {
    if (client && !client.destroyed) {
      client.write('1');
    }
  }, HEART_BEAT_INTERVAL);
}

export const sendData = (data: any) => {
  const jsonStr = JSON.stringify(data);
  client.write(jsonStr);
};
