import React, { useState } from 'react';
import Map from './Map';
import HomePage from './homePage';

function App() {
  const [currentView, setCurrentView] = useState('home');

  const navigateToMap = () => {
    setCurrentView('map');
  };

  const navigateToHome = () => {
    setCurrentView('home');
  };

  return (
    <div className="App">
      {currentView === 'home' ? (
        <HomePage onNavigateToMap={navigateToMap} />
      ) : (
        <Map onNavigateHome={navigateToHome} />
      )}
    </div>
  );
}

export default App;

