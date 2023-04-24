
import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';
import {BrowserRouter} from "react-router-dom";
import reportWebVitals from './components/reportWebVitals';
import { AccountProvider } from './components/Auth';
import DonateCard from './components/Donate'
import Comments from './components/Comments';
import Subscribe from './components/Subscribe';
const rootElement = document.getElementById('wallet');
const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <AccountProvider>
      <App />
    </AccountProvider>
  </React.StrictMode>
);
//
// const commentsElement = document.getElementById('comments');
// const commentsRoot = ReactDOM.createRoot(commentsElement);
// commentsRoot.render(
//   <React.StrictMode>
//     <BrowserRouter>
//       <AccountProvider>
//         <Comments />
//       </AccountProvider>
//     </BrowserRouter>
//   </React.StrictMode>
// );

const subscribeEle = document.getElementById('subscribe');
const subscribeRoot = ReactDOM.createRoot(subscribeEle);
subscribeRoot.render(
    <React.StrictMode>
        <BrowserRouter>
            <AccountProvider>
                <Subscribe />
            </AccountProvider>
        </BrowserRouter>
    </React.StrictMode>
);

// const donateElement = document.getElementById('donate');
// const donateRoot = ReactDOM.createRoot(donateElement);
// donateRoot.render(
//   <React.StrictMode>
//     <DonateCard />
//   </React.StrictMode>
// );

reportWebVitals(console.log);
