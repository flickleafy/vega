import React, { useEffect, useState } from 'react';
import DisplayPanel from '../DisplayPanel';
import styles from './styles.module.css';
import { DataInterface } from '../../interfaces/DataInterface';

export interface StatusSectionProps {
  data: DataInterface;
}

const StatusSection = ({ data }: StatusSectionProps) => {
  // State hooks for each control and display
  const [gpuClock, setGpuClock] = useState(0);
  const [memoryClock, setMemoryClock] = useState(0);
  const [coreVoltage, setCoreVoltage] = useState(0);
  const [temperature, setTemperature] = useState(0);

  useEffect(() => {
    if (data) {
      data?.gpus[0] && setTemperature(data.gpus[0].currentDegree);
      data?.gpus[0] && setGpuClock(data.gpus[0].coreClock);
      data?.gpus[0] && setMemoryClock(data.gpus[0].ramClock);
      data?.gpus[0] && setCoreVoltage(data.gpus[0].coreVoltage);
    }
  }, [data]);

  return (
    <div>
      <div className={styles.statusDisplaySection}>
        {/* Display for top-level status indicators */}
        <DisplayPanel
          label='GPU'
          value={gpuClock}
          maxValue={5000}
          unitSymbol='MHz'
        />
        <DisplayPanel
          label='MEM'
          value={memoryClock}
          maxValue={5000}
          unitSymbol='MHz'
        />
        <DisplayPanel
          label='VOLT'
          value={coreVoltage}
          maxValue={1100}
          unitSymbol='mV'
        />
        <DisplayPanel
          label='TEMP'
          value={Number(temperature)}
          maxValue={100}
          unitSymbol='°C'
        />
      </div>
    </div>
  );
};

export default StatusSection;
