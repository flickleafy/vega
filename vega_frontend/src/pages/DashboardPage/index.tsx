import React, { useEffect, useState } from 'react';
import { DataInterface } from '../../interfaces/DataInterface';
import styles from './styles.module.css';
import StatusCard from '../../components/StatusCard';
import { rawDataToCardDataFormatAdapter } from './dataAdapter';
import { Devices, Properties } from './interfaces';

interface DashboardPageProps {
  data: DataInterface | null;
}

/**
 * DashboardPage displays an overview of the hardware status,
 * including CPU, GPUs, and other devices.
 */
const DashboardPage: React.FC<DashboardPageProps> = ({ data }) => {
  const [cards, setCards] = useState<Devices>({});
  useEffect(() => {
    if (data) {
      const array = rawDataToCardDataFormatAdapter(data);
      setCards(array);
    }
  }, [data]);
  return (
    <div className={styles.dashboard}>
      {Object.entries(cards).map((device) => {
        const deviceName: string = device[0] as unknown as string;
        const properties: Properties = device[1];
        return (
          <StatusCard
            key={deviceName}
            title={deviceName.toUpperCase()}
            properties={properties}
          />
        );
      })}
    </div>
  );
};

export default DashboardPage;
