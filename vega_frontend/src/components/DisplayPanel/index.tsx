import React from 'react';
import styles from './styles.module.css';

export interface DisplayPanelProps {
  label: string;
  value: number;
  maxValue: number;
  unitSymbol: string;
}

const DisplayPanel = ({
  label,
  value,
  maxValue,
  unitSymbol,
}: DisplayPanelProps) => {
  const fillPercentage = Math.min(value / maxValue, 1);

  // Function to create meter blocks
  const renderMeterBlocks = () => {
    const blocks = [];
    const totalBlocks = 20; // Total number of blocks in the meter
    const filledBlocks = Math.round(fillPercentage * totalBlocks);

    for (let i = 0; i < totalBlocks; i++) {
      blocks.push(
        <div
          key={i}
          className={
            i < filledBlocks
              ? styles.displayPanelFilledBlock
              : styles.displayPanelEmptyBlock
          }
        />
      );
    }

    return blocks;
  };

  return (
    <div className={styles.displayPanelContainer}>
      <label className={styles.displayPanelLabel}>{label}</label>
      <div className={styles.displayPanelMeter}>{renderMeterBlocks()}</div>
      <div className={styles.displayPanelValue}>
        {value} {unitSymbol}
      </div>
    </div>
  );
};

export default DisplayPanel;
