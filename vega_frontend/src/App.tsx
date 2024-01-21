import React, { useEffect, useState } from 'react';
import SplashScreen from './pages/SplashScreen';
import Main from './pages/Main';

export function App() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setTimeout(() => setLoading(false), 3000);
  }, []);

  return <>{loading ? <SplashScreen /> : <Main />}</>;
}
