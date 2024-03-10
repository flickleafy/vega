import {
  CpuDataInterface,
  DataInterface,
  GpuDataInterface,
  WatercoolerDataInterface,
} from '../interfaces/DataInterface';
import { ApiDataDTO } from '../interfaces/ApiDataDTO';

export function apiDataAdapter(
  apiData: ApiDataDTO
): React.SetStateAction<DataInterface> {
  // GPU data adaptation
  const gpus: GpuDataInterface[] = [
    {
      currentDegree: apiData.gpu0_degree,
      averageDegree: apiData.gpu0_average_degree,
      coreClock: 0, // No corresponding field in ApiDataDTO
      coreVoltage: 0, // No corresponding field in ApiDataDTO
      ramClock: 0, // No corresponding field in ApiDataDTO
      ramVoltage: 0, // No corresponding field in ApiDataDTO
      powerLimit: 0,
      temperatureLimit: 0,
      fans: [
        {
          currentFanSpeed: apiData.gpu0_c_fan_speed1,
          setFanSpeed: apiData.gpu0_s_fan_speed1,
        },
        {
          currentFanSpeed: apiData.gpu0_c_fan_speed2,
          setFanSpeed: apiData.gpu0_s_fan_speed2,
        },
      ],
    },
    {
      currentDegree: apiData.gpu1_degree,
      averageDegree: apiData.gpu1_average_degree,
      coreClock: 0,
      coreVoltage: 0,
      ramClock: 0,
      ramVoltage: 0,
      powerLimit: 0,
      temperatureLimit: 0,
      fans: [
        {
          currentFanSpeed: apiData.gpu1_c_fan_speed1,
          setFanSpeed: apiData.gpu1_s_fan_speed1,
        },
        {
          currentFanSpeed: apiData.gpu1_c_fan_speed2,
          setFanSpeed: apiData.gpu1_s_fan_speed2,
        },
      ],
    },
  ];

  // CPU data adaptation
  const cpu: CpuDataInterface = {
    currentDegree: apiData.cpu_degree,
    averageDegree: apiData.cpu_average_degree,
  };

  // Water cooler data adaptation
  const watercooler: WatercoolerDataInterface = {
    currentDegree: apiData.wc_degree,
    averageDegree: apiData.wc_average_degree,
    fanSpeed: apiData.wc_fan_speed,
    fanPercent: apiData.wc_fan_percent,
    pumpSpeed: apiData.wc_pump_speed,
    arrayColor: apiData.array_color,
  };

  return {
    cpu,
    watercooler,
    gpus,
  };
}
