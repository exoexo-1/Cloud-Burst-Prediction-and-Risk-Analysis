import React from 'react';
import './homePage.css';

const HomePage = ({ onNavigateToMap }) => {
  return (
    <div className="homepage-container">
      <header className="homepage-header">
        <div className="logo">Hydroprognosis</div>
        <button className="register-btn">Register</button>
      </header>
      <main className="main-content">
        <h1 className="title">Hydroprognosis</h1>
        <p className="subtitle">Cloud Burst Prediction and Impact Analysis</p>
        <button className="map-btn" onClick={onNavigateToMap}>
          Analyze on Map
        </button>
      </main>
    </div>
  );
};

export default HomePage;
