// See the Electron documentation for details on how to use preload scripts:
// https://www.electronjs.org/docs/latest/tutorial/process-model#preload-scripts

import { contextBridge, ipcRenderer, IpcRendererEvent } from 'electron';

export type Channels = 'message' | 'update-setting' | 'data';

const electronHandler = {
  ipcRenderer: {
    sendMessage(channel: Channels, args: unknown[]) {
      ipcRenderer.send(channel, args);
      // let validChannels = ['update-setting'];
      // if (validChannels.includes(channel)) {
      //   ipcRenderer.send(channel, data);
      // }
    },
    on(channel: Channels, func: (...args: unknown[]) => void) {
      const subscription = (_event: IpcRendererEvent, ...args: unknown[]) =>
        func(...args);
      ipcRenderer.on(channel, subscription);
      // let validChannels = ['update-setting-response'];
      // if (validChannels.includes(channel)) {
      //   // Deliberately strip event as it includes `sender`
      //   ipcRenderer.on(channel, (event, ...args) => func(...args));
      // }
      return () => {
        ipcRenderer.removeListener(channel, subscription);
      };
    },
    once(channel: Channels, func: (...args: unknown[]) => void) {
      ipcRenderer.once(channel, (_event, ...args) => func(...args));
    },
  },
};

contextBridge.exposeInMainWorld('electron', electronHandler);

export type ElectronHandler = typeof electronHandler;
