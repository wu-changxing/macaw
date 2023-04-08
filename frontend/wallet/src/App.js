import { Route, Routes } from 'react-router-dom';
import WalletCardEthers from'./components/WalletCardEthers';
import Section from "./components/Auth"

import {AccountProvider} from "./components/Auth"

function App() {

  return (
    <div className="space-y-20">

      <WalletCardEthers/>
 
    </div>
  );
}

export default App;
