import React from 'react';
import styles from './styles.module.css';
import NavigationBar from '../../components/NavigationBar';

export interface PageTemplateProps {
  pages: string[];
  selectedPage: string;
  onSelectPage: (option: string) => void;
  children: JSX.Element;
}

const PageTemplate = ({
  pages,
  selectedPage,
  onSelectPage,
  children,
}: PageTemplateProps) => {
  return (
    <div className={styles.mainApp}>
      <div
        className={`${styles.column} ${styles.side} ${styles.contentCenter}`}>
        <NavigationBar
          options={pages}
          selectedOption={selectedPage}
          onSelect={onSelectPage}
        />
      </div>
      {children}
    </div>
  );
};

export default PageTemplate;
