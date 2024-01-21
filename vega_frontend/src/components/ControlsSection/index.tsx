import React, { ChangeEvent, useEffect, useState } from 'react';
import SliderComponent from '../SliderComponent';
import ToggleButton from '../ToggleButton';
import styles from './styles.module.css';
import { CoolingDataInterface } from '../../interfaces/CoolingDataInterface';

export interface ConstrolsSectionProps {
  data: CoolingDataInterface;
}

const ConstrolsSection = ({ data }: ConstrolsSectionProps) => {
  // State hooks for each control and display
  const [gpuClock, setGpuClock] = useState(0);
  const [memoryClock, setMemoryClock] = useState(0);
  const [coreVoltage, setCoreVoltage] = useState(0);
  const [fanSpeed1, setFanSpeed1] = useState(0);
  const [fanSpeed2, setFanSpeed2] = useState(0);
  const [powerLimit, setPowerLimit] = useState(0);
  const [tempLimit, setTempLimit] = useState(0);
  const [fanSyncEnabled, setFanSyncEnabled] = useState(false);

  useEffect(() => {
    if (data) {
      // data?.gpu0_degree && setTemperature(data.gpu0_degree);
      data?.gpu0_c_fan_speed1 && setFanSpeed1(data.gpu0_c_fan_speed1);
      data?.gpu0_c_fan_speed2 && setFanSpeed2(data.gpu0_c_fan_speed2);
    }
  }, [data]);

  // Slider change handlers
  const handleSliderChange =
    (setter: React.Dispatch<React.SetStateAction<number>>) =>
    (event: ChangeEvent<HTMLInputElement>) => {
      setter(Number(event.target.value));
    };

  const toggleFanSync = () => setFanSyncEnabled(!fanSyncEnabled);

  return (
    <div className={styles.controlsContainer}>
      <div className={styles.leftControlsSection}>
        <div className={styles.sectionTitle}>Voltage</div>
        <SliderComponent
          label='Core Voltage'
          min={0}
          max={2000}
          value={coreVoltage}
          unitSymbol='mV'
          onChange={handleSliderChange(setCoreVoltage)}
          settingName='core_voltage'
        />
      </div>
      <div className={styles.midControlsSection}>
        <div className={styles.sectionTitle}>Clock</div>
        <SliderComponent
          label='GPU Clock'
          min={0}
          max={2000}
          value={gpuClock}
          unitSymbol='MHz'
          onChange={handleSliderChange(setGpuClock)}
          settingName='gpu_clock'
        />
        <SliderComponent
          label='Memory Clock'
          min={0}
          max={5000}
          value={memoryClock}
          unitSymbol='MHz'
          onChange={handleSliderChange(setMemoryClock)}
          settingName='memory_clock'
        />
      </div>
      <div className={styles.rightControlsSection}>
        <div className={styles.sectionTitle}>Fan</div>
        <SliderComponent
          label='Power Limit'
          min={0}
          max={100}
          value={powerLimit}
          unitSymbol='%'
          onChange={handleSliderChange(setPowerLimit)}
          settingName='power_limit'
        />
        <SliderComponent
          label='Temp Limit'
          min={0}
          max={100}
          value={tempLimit}
          unitSymbol='°C'
          onChange={handleSliderChange(setTempLimit)}
          settingName='temp_limit'
        />
        <SliderComponent
          label='Fan1 Speed'
          min={0}
          max={100}
          value={fanSpeed1}
          unitSymbol='%'
          onChange={handleSliderChange(setFanSpeed1)}
          settingName='fan_speed_1'
        />
        <SliderComponent
          label='Fan2 Speed'
          min={0}
          max={100}
          value={fanSpeed2}
          unitSymbol='%'
          onChange={handleSliderChange(setFanSpeed2)}
          settingName='fan_speed_2'
        />
        <ToggleButton
          label='Fan Sync'
          isEnabled={fanSyncEnabled}
          onToggle={toggleFanSync}
        />
      </div>
    </div>
  );
};

export default ConstrolsSection;
