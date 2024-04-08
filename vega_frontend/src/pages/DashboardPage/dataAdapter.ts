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
  fanPercent: 'Fan %',
  fanSpeed: 'Fan Speed',
  pumpSpeed: 'Pump Speed',
  arrayColor: 'Color',
};

export const dataToCardAdapter = (data: DataInterface): Devices => {
  const devicesRecord: Devices = {};

  Object.entries(data).forEach(([title, deviceData]) => {
    if (Array.isArray(deviceData)) {
      deviceData.forEach((deviceData2, index) => {
        propertiesProcessor(deviceData2, title, index, devicesRecord);
      });
    } else {
      const deviceTitle = fieldsDictionary[title];
      propertiesProcessor(deviceData, deviceTitle, null, devicesRecord);
    }
  });
  return devicesRecord;
};

function propertiesProcessor(
  deviceData: any,
  deviceTitle: string,
  deviceIndex: number | null,
  devicesRecord: any
) {
  if (deviceIndex !== null) {
    deviceTitle = `${fieldsDictionary[deviceTitle]} ${deviceIndex + 1}`;
  }
  devicesRecord[deviceTitle] = {};

  Object.entries(deviceData).forEach(([title, propertyData]) => {
    if (Array.isArray(propertyData)) {
      if (title === 'arrayColor') {
        const propertyTitle = fieldsDictionary[title];
        devicesRecord[deviceTitle][
          propertyTitle
        ] = `${propertyData[0]} ${propertyData[1]} ${propertyData[2]}`;
      } else {
        propertyData.forEach((propertyData1, propertyIndex) => {
          propertiesProcessor(
            propertyData1,
            title,
            propertyIndex,
            devicesRecord[deviceTitle]
          );
        });
      }
    } else {
      const propertyTitle = fieldsDictionary[title];
      devicesRecord[deviceTitle][propertyTitle] = deviceData[title];
    }
  });
}
