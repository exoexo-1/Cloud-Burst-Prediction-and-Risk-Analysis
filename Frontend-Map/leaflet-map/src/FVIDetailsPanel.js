import React, { useEffect, useState } from 'react';
import './FVIDetailsPanel.css';

const FVIDetailsPanel = ({ isOpen, onClose, position, fvi, placeName }) => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch LLM analysis when FVI data changes
  useEffect(() => {
    if (isOpen && fvi && position) {
      setLoading(true);
      fetch(`https://fuzzy-api-3e87.onrender.com/analysis?place_name=${placeName}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(fvi), // Send FVI data to backend
      })
        .then(res => res.json())
        .then(data => {
          setAnalysis(data.report?.analysis || data.report);
          setLoading(false);
        })
        .catch(err => {
          console.error("Error fetching analysis:", err);
          setAnalysis("Error fetching analysis report.");
          setLoading(false);
        });
    }
  }, [isOpen, fvi, position, placeName]);

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
            {/* Location Info */}
            <div className="location-info">
              <h4>📍 Location Information</h4>
              <div className="info-card">
                <p><strong>Place:</strong> {placeName}</p>
                <p><strong>Coordinates:</strong> {position.lat.toFixed(4)}, {position.lng.toFixed(4)}</p>
                <p><strong>FVI Score:</strong> <span className="fvi-score">{fvi.fvi_score}/100</span></p>
                <p><strong>Risk Level:</strong> {fvi.risk_level}</p>
              </div>
            </div>

            {/* Key Factors */}
            <div className="key-factors">
              <h4>🔑 Key Factors</h4>
              <div className="factors-list">
                {fvi.key_factors && fvi.key_factors.map((factor, idx) => (
                  <div key={idx} className="factor-item">
                    • {factor}
                  </div>
                ))}
              </div>
            </div>

            {/* LLM Analysis */}
            <div className="detailed-analysis">
              <h4>📊 Risk Analysis Report</h4>
              <div className="analysis-card">
                {loading ? (
                  <p>⏳ Generating AI analysis...</p>
                ) : (
                  <pre style={{ whiteSpace: "pre-wrap", fontSize: "14px" }}>
                    {analysis}
                  </pre>
                )}
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
