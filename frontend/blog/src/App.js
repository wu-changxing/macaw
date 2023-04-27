import React from 'react';
import { BrowserRouter as Router,Routes, Route,  } from 'react-router-dom';
import FlexPage from './components/FlexPage';
import FlexPageList from './FlexPageList';
function App() {
  return (
 <Router>
      <div className="App">
        <Routes>
          <Route path="/engineer/:slug" element={<FlexPage />} />
          {/* Add other routes here */}
        <Route path="/flexpages" element={<FlexPageList />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
