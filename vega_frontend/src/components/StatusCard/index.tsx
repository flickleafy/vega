import React from 'react';
import styles from './styles.module.css';

interface StatusCardProps {
  title: string;
  properties: Record<string, any>;
}

/**
 * StatusCard displays the status of a hardware component.
 */
const StatusCard: React.FC<StatusCardProps> = ({ title, properties }) => {
  // Function to render property values, including handling of nested objects
  const renderPropertyValue = (value: any): JSX.Element | string => {
    if (typeof value === 'object' && value !== null) {
      return (
        <div style={{ paddingLeft: '20px' }}>
          {Object.entries(value).map(([key, val]) => (
            <div key={key}>
              {key}: {renderPropertyValue(val)}
            </div>
          ))}
        </div>
      );
    }
    return value.toString();
  };

  // Render the card with the hardware status
  return (
    <div className={styles.card}>
      <h2 className={styles.cardTitle}>{title}</h2>
      {Object.entries(properties).map(([key, value]) => (
        <div
          key={key}
          className={styles.cardContent}>
          {key}: {renderPropertyValue(value)}
        </div>
      ))}
    </div>
  );
};

export default StatusCard;
