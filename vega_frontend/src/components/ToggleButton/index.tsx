import React from 'react';
import styles from './styles.module.css';

export interface ToggleButtonProps {
  label: string;
  isEnabled: boolean;
  onToggle: () => void;
}

const ToggleButton = ({ label, isEnabled, onToggle }: ToggleButtonProps) => {
  return (
    <div className='toggle-container'>
      <label>{label}</label>
      <button
        className={isEnabled ? 'enabled' : ''}
        onClick={onToggle}>
        {isEnabled ? 'ON' : 'OFF'}
      </button>
    </div>
  );
};

export default ToggleButton;
