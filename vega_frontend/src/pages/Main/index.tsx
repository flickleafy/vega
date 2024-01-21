import React, { useEffect, useState } from 'react';
import { CoolingDataInterface } from '../../interfaces/CoolingDataInterface';
import StatusSection from '../../components/StatusSection';
import StatusSectionSvg from '../../components/StatusSectionSvg';
import ControlsSection from '../../components/ControlsSection';
const { ipcRenderer } = window.electron;
import styles from './styles.module.css';

/**
 * The Main component for the overclocking application interface.
 * It manages the states and behavior of various sliders and displays
 * for controlling and monitoring the GPU settings.
 */
const Main = () => {
  const [data, setData] = useState(null);
  useEffect(() => {
    const handleSettingUpdateResponse = (_event: any, response: any) => {
      console.log('Setting was updated:', response);
      // Handle the response, update state, etc.
    };
    // ipcRenderer.on('update-setting-response', handleSettingUpdateResponse);
  }, []);

  useEffect(() => {
    const handleData = (data: CoolingDataInterface) => {
      data && setData(data);
    };
    ipcRenderer.on('data', handleData);
  }, []);

  return (
    <div className={styles.mainApp}>
      <StatusSection data={data} />
      {/* <StatusSectionSvg data={data} /> */}
      <ControlsSection data={data} />
    </div>
  );
};

export default Main;
