import { DataInterface } from '../../interfaces/DataInterface';
import { Devices, Properties } from './interfaces';

const fieldsDictionary: Record<string, string> = {
  currentDegree: 'Degree',
  averageDegree: 'Aver. Degree',
  coreClock: 'Core Clock',
  coreVoltage: 'Core Volt.',
  ramClock: 'Ram Clock',
  ramVoltage: 'Ram Volt.',
  powerLimit: 'Power Limit',
  temperatureLimit: 'Temp. Limit',
  fans: 'Fan',
  gpus: 'Gpu',
  cpu: 'Cpu',
  watercooler: 'Watercooler',
  currentFanSpeed: 'Current Speed',
  setFanSpeed: 'Set Speed',
};

export const dataToCardAdapter = (data: DataInterface): Devices => {
  console.log('entry');
  const devicesRecord: Devices = {};

  Object.entries(data).forEach(([title, deviceData]) => {
    if (Array.isArray(deviceData)) {
      deviceData.forEach((deviceData2, index) => {
        propertiesProcessor(deviceData2, title, index, devicesRecord);
      });
    } else {
      const deviceTitle = fieldsDictionary[title];
      console.log('devicetitle', deviceTitle, 'deviceData', deviceData);
      devicesRecord[deviceTitle] = deviceData;
    }
  });

  // console.log(JSON.stringify(devicesRecord, null, 4));
  return devicesRecord;
};

function propertiesProcessor(
  deviceData: any,
  deviceTitle: string,
  deviceIndex: number,
  devicesRecord: Devices
) {
  // console.log('deviceData2', deviceData);
  deviceTitle = `${fieldsDictionary[deviceTitle]} ${deviceIndex + 1}`;
  devicesRecord[deviceTitle] = {};

  Object.entries(deviceData).forEach(([title, propertyData]) => {
    if (Array.isArray(propertyData)) {
      propertyData.forEach((propertyData1, propertyIndex) => {
        const propertyTitle = `${fieldsDictionary[title]} ${propertyIndex + 1}`;
        // console.log('title', title);
        devicesRecord[deviceTitle][propertyTitle] = propertyData1;
        // console.log('propertyDataArray', propertyTitle, propertyData1);
      });
    } else {
      const propertyTitle = fieldsDictionary[title];
      // console.log('propertyDataNonArray', propertyTitle, propertyData);
      devicesRecord[deviceTitle][propertyTitle] = deviceData[title];
      // devicesRecord[deviceTitle] = propertyData;
    }
  });
}
