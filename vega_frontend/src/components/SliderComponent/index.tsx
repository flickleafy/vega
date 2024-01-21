import React, { ChangeEvent } from 'react';
import styles from './styles.module.css';

export interface SliderComponentProps {
  label: string;
  min: number;
  max: number;
  value: number;
  unitSymbol: string;
  settingName: string;
  onChange: (event: ChangeEvent<HTMLInputElement>) => void;
}

const SliderComponent = ({
  label,
  min,
  max,
  value,
  unitSymbol,
  onChange,
  settingName,
}: SliderComponentProps) => {
  const handleSliderChange = (event: ChangeEvent<HTMLInputElement>) => {
    const newValue = event.target.value;
    if (value && newValue) {
      onChange(event); // This updates the local state
      window.electron.ipcRenderer.sendMessage('update-setting', [
        settingName,
        newValue,
      ]);
    }
  };

  return (
    <div className={styles.sliderContainer}>
      <div className={styles.firstCell}>
        <label className={styles.sliderLabelLeft}>{label}</label>
        <input
          className={styles.rangeInput}
          type='range'
          min={min}
          max={max}
          value={value}
          onChange={handleSliderChange}
        />
      </div>
      <div className={styles.secondCell}>
        <label className={styles.sliderLabelRight}>({unitSymbol})</label>
        <span className={styles.valueDisplay}>{value}</span>
      </div>
    </div>
  );
};

export default SliderComponent;
