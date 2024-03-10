import React, { useEffect, useState } from 'react';
import DisplayPanel from '../DisplayPanel';
import styles from './styles.module.css';
import { DataInterface } from '../../interfaces/DataInterface';

export interface StatusSectionProps {
  data: DataInterface;
}

const calculateDashArray = (value: number, max: number) => {
  const circumference = 2 * Math.PI * 100;
  const percentage = value / max;
  return `${circumference * percentage} ${circumference * (1 - percentage)}`;
};

const StatusSection = ({ data }: StatusSectionProps) => {
  const [gpuClock, setGpuClock] = useState(0);
  const [memoryClock, setMemoryClock] = useState(0);
  const [coreVoltage, setCoreVoltage] = useState(0);
  const [temperature, setTemperature] = useState(0);

  useEffect(() => {
    if (data) {
      setTemperature(data.gpu0_degree);
    }
  }, [data]);

  const gpuClockDashArray = calculateDashArray(gpuClock, 2000);
  const memoryClockDashArray = calculateDashArray(memoryClock, 5000);
  const coreVoltageDashArray = calculateDashArray(coreVoltage, 1200); // Assuming 1200mV is the max voltage
  const temperatureDashArray = calculateDashArray(temperature, 100); // Assuming 100°C is the max temperature

  return (
    <div>
      <div className={styles.statusDisplaySection}>
        {/* SVG Gauges */}
        {Gauges(gpuClockDashArray, gpuClock, temperatureDashArray, temperature)}
      </div>
    </div>
  );
};

export default StatusSection;

function Gauges(
  gpuClockDashArray: string,
  gpuClock: number,
  temperatureDashArray: string,
  temperature: number
) {
  return (
    <svg
      width='600'
      height='300'
      viewBox='0 0 600 300'
      xmlns='http://www.w3.org/2000/svg'>
      {/* GPU Clock Gauge */}
      <circle
        cx='150'
        cy='150'
        r='100'
        fill='none'
        stroke='#555'
        strokeWidth='10'
      />
      <circle
        cx='150'
        cy='150'
        r='100'
        fill='none'
        stroke='blue'
        strokeWidth='10'
        strokeDasharray={gpuClockDashArray}
        strokeDashoffset='315'
      />
      <text
        x='150'
        y='160'
        fontFamily='Arial'
        fontSize='20'
        fill='white'
        textAnchor='middle'>
        GPU Clock
      </text>
      <text
        x='150'
        y='190'
        fontFamily='Arial'
        fontSize='16'
        fill='white'
        textAnchor='middle'>{`${gpuClock} MHz`}</text>

      {/* Memory Clock Gauge */}
      <circle
        cx='450'
        cy='150'
        r='100'
        fill='none'
        stroke='#555'
        strokeWidth='10'
      />
      <circle
        cx='450'
        cy='150'
        r='100'
        fill='none'
        stroke='blue'
        strokeWidth='10'
        strokeDasharray={temperatureDashArray}
        strokeDashoffset='315'
      />
      <text
        x='450'
        y='160'
        fontFamily='Arial'
        fontSize='20'
        fill='white'
        textAnchor='middle'>
        Temperature
      </text>
      <text
        x='450'
        y='190'
        fontFamily='Arial'
        fontSize='16'
        fill='white'
        textAnchor='middle'>{`${temperature} °C`}</text>

      {/* Add more circles and text for core voltage and temperature as needed */}
      {/* ... */}
    </svg>
  );
}
