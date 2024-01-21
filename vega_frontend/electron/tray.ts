import { app, Tray, Menu, BrowserWindow } from 'electron';
import path from 'path';
import { generateTrayIconWithText } from './iconFromText';
const iconPath = path.join(__dirname, '../../assets/icons/icon.png');
let trayStats: Tray | null = null;

export function createTray(
  tray: Tray | null,
  mainWindow: BrowserWindow | null
) {
  tray = new Tray(iconPath);
  trayStats = new Tray(iconPath);
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Open',
      click: function () {
        mainWindow.show();
      },
    },
    {
      label: 'Hide',
      click: function () {
        mainWindow.hide();
      },
    },
    {
      label: 'Quit',
      click: function () {
        // app.isQuiting = true;
        app.quit();
      },
    },
  ]);

  tray.setToolTip('VEGA Suit');
  tray.setContextMenu(contextMenu);

  setInterval(async () => {
    const metrics = 'C 50%'; // Replace this with your actual metrics
    const iconStatsPath = await generateTrayIconWithText(metrics);
    trayStats.setImage(iconStatsPath);
  }, 5000); // Update every 5 seconds
}
