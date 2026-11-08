import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';
import { AccountProvider } from './components/Auth';

const rootElement = document.getElementById('wallet');
const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <AccountProvider>
      <App />
    </AccountProvider>
  </React.StrictMode>
);
