import React from 'react';
import { createRoot } from 'react-dom/client'; // Import createRoot
import { App } from './App';

const container = document.getElementById('root'); // Get the root element
const root = createRoot(container); // Create a root

root.render(<App />); // Use the new render method
