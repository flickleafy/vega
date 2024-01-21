import React from 'react';
import styles from './styles.module.css'; // Import as a module to use the classes

const SplashScreen = () => {
  return (
    <div className={styles.splashContainer}>
      <div className={styles.loadingWrapper}>
        <div className={styles.loadingCircle}></div>
        <div className={styles.loadingText}>Loading</div>
      </div>
    </div>
  );
};

export default SplashScreen;
