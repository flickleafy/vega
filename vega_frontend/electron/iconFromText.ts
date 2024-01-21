import Jimp from 'jimp';
import path from 'path';
import * as os from 'os';
export const fontPath = path.join(
  __dirname,
  '../../assets/fonts/open-sans-12-black.fnt'
);

export const generateTrayIconWithText = async (text: string) => {
  const font = await Jimp.loadFont(fontPath);
  const image = new Jimp(32, 32, '#ffffffff'); // Creating a white 64x64 image

  image.print(font, 0, 0, text, 32); // Add text to image

  const tempPath = path.join(os.tmpdir(), 'tray-icon.png');
  await image.writeAsync(tempPath); // Write image to temp file

  return tempPath;
};
