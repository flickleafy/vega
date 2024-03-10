import React from 'react';
import styles from './styles.module.css';

export interface NavigationBarProps {
  options: string[];
  selectedOption: string;
  onSelect: (option: string) => void;
}

const NavigationBar = ({
  options,
  selectedOption,
  onSelect,
}: NavigationBarProps) => {
  return (
    <div className={styles.selectionBar}>
      {options.map((option) => (
        <div
          key={option}
          className={`${styles.option} ${
            selectedOption === option ? styles.selected : ''
          }`}
          onClick={() => onSelect(option)}>
          {option}
        </div>
      ))}
    </div>
  );
};

export default NavigationBar;
