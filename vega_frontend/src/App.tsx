import React, { useEffect, useState } from 'react';
import SplashScreen from './pages/SplashScreen';
import PageTemplate from './components/PageTemplate';
import GpuPage from './pages/GpuPage';
import { DataInterface } from './interfaces/DataInterface';
import { ApiDataDTO } from './interfaces/ApiDataDTO';
import { apiDataAdapter } from './adapters/apiDataAdapter';
const { ipcRenderer } = window.electron;

export function App() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<DataInterface | null>(null);
  const [selectedPage, setSelectedPage] = useState('GPU');
  const pagesTitle = ['Dash', 'CPU', 'GPU'];
  const pagesComponents: Record<string, JSX.Element> = {
    CPU: <></>,
    Dash: <></>,
    GPU: (
      <GpuPage
        key={1}
        data={data}
      />
    ),
  };

  useEffect(() => {
    setTimeout(() => setLoading(false), 3000);
  }, []);

  useEffect(() => {
    const handleData = (data: ApiDataDTO) => {
      data && setData(apiDataAdapter(data));
    };
    ipcRenderer.on('data', handleData);
  }, []);

  const handleSelectPage = (page: string) => {
    setSelectedPage(page);
  };

  return (
    <>
      {loading ? (
        <SplashScreen />
      ) : (
        <PageTemplate
          pages={pagesTitle}
          onSelectPage={handleSelectPage}
          selectedPage={selectedPage}>
          {pagesComponents[selectedPage]}
        </PageTemplate>
      )}
    </>
  );
}
