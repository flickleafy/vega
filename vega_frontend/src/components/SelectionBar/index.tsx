import React from 'react';
import styles from './styles.module.css';

export interface SelectionBarProps {
  options: string[];
  selectedOption: string;
  onSelect: (option: string) => void;
}

const SelectionBar = ({
  options,
  selectedOption,
  onSelect,
}: SelectionBarProps) => {
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

export default SelectionBar;
