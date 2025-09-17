import React from 'react';
import './FVIDetailsPanel.css';

const FVIDetailsPanel = ({ isOpen, onClose, position, fvi, placeName }) => {
  return (
    <div className={`fvi-details-panel ${isOpen ? 'open' : ''}`}>
      <div className="fvi-panel-header">
        <h3>FVI Details</h3>
        <button className="close-panel-btn" onClick={onClose}>
          ×
        </button>
      </div>
      
      <div className="fvi-panel-content">
        {position && fvi ? (
          <>
            <div className="location-info">
              <h4>📍 Location Information</h4>
              <div className="info-card">
                <p><strong>Place:</strong> {placeName}</p>
                <p><strong>Coordinates:</strong> {position.lat.toFixed(4)}, {position.lng.toFixed(4)}</p>
                <p><strong>FVI Score:</strong> <span className="fvi-score">{fvi.fvi_score}/100</span></p>
              </div>
            </div>

            <div className="key-factors">
              <h4>🔑 Key Factors</h4>
              <div className="factors-list">
                {fvi.key_factors.map((factor, idx) => (
                  <div key={idx} className="factor-item">
                    • {factor}
                  </div>
                ))}
              </div>
            </div>

            <div className="detailed-analysis">
              <h4>📊 Detailed Analysis</h4>
              <div className="analysis-card">
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.</p>
                
                <div className="metric-row">
                  <div className="metric">
                    <span className="metric-label">Risk Level:</span>
                    <span className="metric-value high">High</span>
                  </div>
                  <div className="metric">
                    <span className="metric-label">Confidence:</span>
                    <span className="metric-value medium">85%</span>
                  </div>
                </div>

                <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
              </div>
            </div>

            <div className="environmental-data">
              <h4>🌍 Environmental Data</h4>
              <div className="env-grid">
                <div className="env-item">
                  <span className="env-label">Temperature:</span>
                  <span className="env-value">24°C</span>
                </div>
                <div className="env-item">
                  <span className="env-label">Humidity:</span>
                  <span className="env-value">65%</span>
                </div>
                <div className="env-item">
                  <span className="env-label">Wind Speed:</span>
                  <span className="env-value">12 km/h</span>
                </div>
                <div className="env-item">
                  <span className="env-label">Precipitation:</span>
                  <span className="env-value">0.2mm</span>
                </div>
              </div>
            </div>

            <div className="recommendations">
              <h4>💡 Recommendations</h4>
              <div className="recommendations-list">
                <div className="recommendation-item">
                  {/* <span className="rec-icon">🔥</span> */}
                  <p>Monitor fire weather conditions closely during dry periods</p>
                </div>
                <div className="recommendation-item">
                  {/* <span className="rec-icon">🌊</span> */}
                  <p>Implement water conservation measures</p>
                </div>
                <div className="recommendation-item">
                  {/* <span className="rec-icon">🏠</span> */}
                  <p>Consider vegetation management around structures</p>
                </div>
              </div>
            </div>

            <div className="historical-data">
              <h4>📈 Historical Trends</h4>
              <div className="history-card">
                <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Mauris vel sagittis lorem. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas.</p>
                <div className="trend-indicators">
                  {/* <span className="trend-item">📈 Increasing risk trend</span>
                  <span className="trend-item">⚠️ Seasonal variations detected</span>
                  <span className="trend-item">🎯 Pattern consistency: 78%</span> */}
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="no-data">
            <div className="no-data-icon">🗺️</div>
            <h4>No Location Selected</h4>
            <p>Click on the map to select a location and view detailed FVI analysis.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FVIDetailsPanel;