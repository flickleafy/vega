import React, { useEffect, useState } from 'react';
import styles from './styles.module.css';
import { DataInterface } from '../../interfaces/DataInterface';
import StatusSection from '../../components/StatusSection';
import ControlsSection from '../../components/ControlsSection';
import SelectionBar from '../../components/SelectionBar';
// import StatusSectionSvg from '../../components/StatusSectionSvg';
// const { ipcRenderer } = window.electron;

export interface GpuPageProps {
  data: DataInterface;
}

/**
 * The Main component for the overclocking application interface.
 * It manages the states and behavior of various sliders and displays
 * for controlling and monitoring the GPU settings.
 */
const GpuPage = ({ data }: GpuPageProps) => {
  const [selectedOption, setSelectedOption] = useState('Pe');
  const options = ['P', 'S', 'U'];

  useEffect(() => {
    const handleSettingUpdateResponse = (_event: any, response: any) => {
      console.log('Setting was updated:', response);
      // Handle the response, update state, etc.
    };
    // ipcRenderer.on('update-setting-response', handleSettingUpdateResponse);
  }, []);

  const handleSelectOption = (option: string) => {
    setSelectedOption(option);
    // Handle the option selection, e.g., change monitoring profiles, update settings, etc.
  };

  return (
    <>
      <div className={`${styles.column} ${styles.mid} ${styles.contentCenter}`}>
        <div className={styles.row}>{/* <DeviceSelector /> */}</div>
        <div>
          <StatusSection data={data} />
          {/* <StatusSectionSvg data={data} /> */}
          <ControlsSection data={data} />
        </div>
        <div className={styles.row}></div>
      </div>
      <div
        className={`${styles.column} ${styles.side} ${styles.contentCenter}`}>
        <SelectionBar
          options={options}
          selectedOption={selectedOption}
          onSelect={handleSelectOption}
        />
      </div>
    </>
  );
};

export default GpuPage;
