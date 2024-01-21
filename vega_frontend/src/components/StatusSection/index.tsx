import React, { useEffect, useState } from 'react';
import DisplayPanel from '../DisplayPanel';
import styles from './styles.module.css';
import { CoolingDataInterface } from '../../interfaces/CoolingDataInterface';

export interface StatusSectionProps {
  data: CoolingDataInterface;
}

const StatusSection = ({ data }: StatusSectionProps) => {
  // State hooks for each control and display
  const [gpuClock, setGpuClock] = useState(0);
  const [memoryClock, setMemoryClock] = useState(0);
  const [coreVoltage, setCoreVoltage] = useState(0);
  const [temperature, setTemperature] = useState(0);

  useEffect(() => {
    if (data) {
      data?.gpu0_degree && setTemperature(data.gpu0_degree);
      data?.gpu0_degree && setGpuClock(data.gpu0_core_clock);
      data?.gpu0_degree && setMemoryClock(data.gpu0_mem_clock);
      data?.gpu0_degree && setCoreVoltage(data.gpu0_core_voltage);
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
