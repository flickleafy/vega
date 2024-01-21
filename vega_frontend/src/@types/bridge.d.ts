import { ElectronHandler } from '../../electron/preload';

declare global {
  // eslint-disable-next-line
  interface Window {
    electron: ElectronHandler;
  }
}
