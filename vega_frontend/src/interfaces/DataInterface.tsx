export interface DataInterface {
  cpu: CpuDataInterface;
  watercooler: WatercoolerDataInterface;
  gpus: GpuDataInterface[];
}

export interface CpuDataInterface {
  currentDegree: number;
  averageDegree: number;
}

export interface WatercoolerDataInterface {
  currentDegree: number;
  averageDegree: number;
  fanSpeed: number;
  fanPercent: number;
  pumpSpeed: number;
  arrayColor: number[];
}

export interface GpuDataInterface {
  currentDegree: number;
  averageDegree: number;
  coreClock: number;
  coreVoltage: number;
  ramClock: number;
  ramVoltage: number;
  powerLimit: number;
  temperatureLimit: number;
  fans: GpuFanDataInterface[];
}

export interface GpuFanDataInterface {
  currentFanSpeed: number;
  setFanSpeed: number;
}
