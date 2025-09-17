import React, { useEffect, useState } from 'react';
import './FVIDetailsPanel.css';

const FVIDetailsPanel = ({ isOpen, onClose, position, fvi, placeName }) => {
  const [analysis, setAnalysis] = useState(null);
  const [parsedAnalysis, setParsedAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Parse the structured analysis response with better flexibility
  const parseAnalysis = (rawAnalysis) => {
    if (!rawAnalysis) return null;
    
    // Handle case where analysis might be an object instead of string
    const analysisText = typeof rawAnalysis === 'object' 
      ? JSON.stringify(rawAnalysis, null, 2) 
      : rawAnalysis;

    const sections = {};
    const lines = analysisText.split('\n');
    let currentSection = null;
    let content = [];

    // Define potential section headers we might encounter
    const sectionPatterns = {
      floodRisk: /flood risk level:/i,
      cloudburstProb: /cloudburst probability:/i,
      keyFactors: /key factors:/i,
      historicalContext: /historical.*context:/i,
      recommendations: /recommendations:/i,
      futurePrediction: /future.*prediction:/i
    };

    for (let line of lines) {
      line = line.trim();
      
      // Skip empty lines
      if (!line) continue;

      // Check if this line starts a new section
      let sectionFound = false;
      for (const [sectionKey, pattern] of Object.entries(sectionPatterns)) {
        if (pattern.test(line)) {
          // Save previous section content
          if (currentSection && content.length > 0) {
            sections[currentSection] = currentSection === 'keyFactors' || currentSection === 'recommendations' 
              ? [...content] 
              : content.join(' ');
            content = [];
          }
          
          // Extract value if it's a simple key-value line
          if (sectionKey === 'floodRisk' || sectionKey === 'cloudburstProb') {
            const value = line.split(':')[1]?.trim() || '';
            sections[sectionKey] = sectionKey === 'cloudburstProb' 
              ? { value, reasoning: '' } 
              : value;
          }
          
          currentSection = sectionKey;
          sectionFound = true;
          break;
        }
      }
      
      if (sectionFound) continue;
      
      // Handle content for current section
      if (currentSection) {
        // Extract cloudburst reasoning
        if (currentSection === 'cloudburstProb' && line.toLowerCase().includes('reasoning')) {
          if (sections.cloudburstProb) {
            sections.cloudburstProb.reasoning = line.split(':').slice(1).join(':').trim();
          }
          continue;
        }
        
        // Skip markdown headers
        if (line.startsWith('###') || line.startsWith('##') || line.startsWith('#')) continue;
        
        // Collect list items or paragraph content
        if (line.startsWith('- ') || line.startsWith('* ') || line.startsWith('• ')) {
          content.push(line.substring(2).trim());
        } else if (line.startsWith('**') && line.endsWith('**')) {
          // Handle bold text
          content.push(line.replace(/\*\*/g, ''));
        } else {
          content.push(line);
        }
      }
    }
    
    // Save the last section content
    if (currentSection && content.length > 0) {
      sections[currentSection] = currentSection === 'keyFactors' || currentSection === 'recommendations' 
        ? [...content] 
        : content.join(' ');
    }

    return sections;
  };

  // Fetch LLM analysis when FVI data changes
  useEffect(() => {
    if (isOpen && fvi && position && placeName) {
      setLoading(true);
      setAnalysis(null);
      setParsedAnalysis(null);
      setError(null);

      const requestBody = {
        place_name: placeName,
        fvi_data: fvi
      };

      fetch(`https://fuzzy-api-3e87.onrender.com/analysis`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify(requestBody),
      })
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
      })
      .then(data => {
        if (data.status === "error") {
          setError(data.error || "Unknown error occurred");
        } else {
          const rawAnalysis = data.analysis || "No analysis available.";
          setAnalysis(rawAnalysis);
          setParsedAnalysis(parseAnalysis(rawAnalysis));
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Error fetching analysis:", err);
        setError(err.message || "Failed to fetch analysis");
        setLoading(false);
      });
    }
  }, [isOpen, fvi, position, placeName]);

  const getRiskLevelColor = (level) => {
    if (!level) return '#6c757d';
    const lowercaseLevel = level.toLowerCase();
    if (lowercaseLevel.includes('low')) return '#28a745';
    if (lowercaseLevel.includes('moderate')) return '#ffc107';
    if (lowercaseLevel.includes('high')) return '#fd7e14';
    if (lowercaseLevel.includes('severe') || lowercaseLevel.includes('extreme')) return '#dc3545';
    return '#6c757d';
  };

  const getRiskIcon = (level) => {
    if (!level) return '⚪';
    const lowercaseLevel = level.toLowerCase();
    if (lowercaseLevel.includes('low')) return '🟢';
    if (lowercaseLevel.includes('moderate')) return '🟡';
    if (lowercaseLevel.includes('high')) return '🟠';
    if (lowercaseLevel.includes('severe') || lowercaseLevel.includes('extreme')) return '🔴';
    return '⚪';
  };

  // Render section only if it exists in the parsed analysis
  const renderSection = (title, content, renderFunction) => {
    if (!content) return null;
    
    return (
      <div className="analysis-section">
        <h4>{title}</h4>
        {renderFunction(content)}
      </div>
    );
  };

  return (
    <div className={`fvi-details-panel ${isOpen ? 'open' : ''}`}>
      <div className="fvi-panel-header">
        <h3>🌧️ Flood Risk Analysis Report</h3>
        <button className="close-panel-btn" onClick={onClose}>
          ×
        </button>
      </div>

      <div className="fvi-panel-content">
        {error ? (
          <div className="error-state">
            <div className="error-icon">⚠️</div>
            <h4>Analysis Error</h4>
            <p>{error}</p>
            <button onClick={() => setError(null)}>Try Again</button>
          </div>
        ) : position && fvi ? (
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

            {/* AI Analysis Results */}
            {loading ? (
              <div className="loading-section">
                <h4>🔄 Generating Analysis</h4>
                <div className="loading-card">
                  <div className="loading-spinner"></div>
                  <p>Analyzing current conditions and generating risk assessment...</p>
                </div>
              </div>
            ) : parsedAnalysis ? (
              <>
                {/* Risk Assessment Summary */}
                {(parsedAnalysis.floodRisk || parsedAnalysis.cloudburstProb) && (
                  <div className="risk-summary">
                    <h4>⚡ Risk Assessment Summary</h4>
                    <div className="risk-cards">
                      {parsedAnalysis.floodRisk && (
                        <div className="risk-card flood-risk">
                          <div className="risk-icon">{getRiskIcon(parsedAnalysis.floodRisk)}</div>
                          <div className="risk-content">
                            <span className="risk-label">Flood Risk Level</span>
                            <span 
                              className="risk-value" 
                              style={{ color: getRiskLevelColor(parsedAnalysis.floodRisk) }}
                            >
                              {parsedAnalysis.floodRisk}
                            </span>
                          </div>
                        </div>
                      )}
                      
                      {parsedAnalysis.cloudburstProb && (
                        <div className="risk-card cloudburst-risk">
                          <div className="risk-icon">
                            {parsedAnalysis.cloudburstProb.value && parsedAnalysis.cloudburstProb.value.toLowerCase().includes('yes') ? '⛈️' : '🌤️'}
                          </div>
                          <div className="risk-content">
                            <span className="risk-label">Cloudburst Probability</span>
                            <span 
                              className="risk-value"
                              style={{ 
                                color: parsedAnalysis.cloudburstProb.value && parsedAnalysis.cloudburstProb.value.toLowerCase().includes('yes') ? '#dc3545' : '#28a745' 
                              }}
                            >
                              {parsedAnalysis.cloudburstProb.value || 'Unknown'}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {parsedAnalysis.cloudburstProb?.reasoning && (
                      <div className="reasoning-box">
                        <strong>Analysis:</strong> {parsedAnalysis.cloudburstProb.reasoning}
                      </div>
                    )}
                  </div>
                )}

                {/* Key Factors */}
                {renderSection(
                  "🔑 Key Risk Factors",
                  parsedAnalysis.keyFactors,
                  (factors) => (
                    <div className="factors-grid">
                      {factors.map((factor, idx) => (
                        <div key={idx} className="factor-card">
                          <span className="factor-bullet">•</span>
                          <span className="factor-text">{factor.replace(/\*\*/g, '')}</span>
                        </div>
                      ))}
                    </div>
                  )
                )}

                {/* Historical Context */}
                {renderSection(
                  "🏛️ Historical & Geographical Context",
                  parsedAnalysis.historicalContext,
                  (context) => (
                    <div className="context-card">
                      <p>{context}</p>
                    </div>
                  )
                )}

                {/* Recommendations */}
                {renderSection(
                  "💡 Recommendations",
                  parsedAnalysis.recommendations,
                  (recommendations) => (
                    <div className="recommendations-list">
                      {recommendations.map((rec, idx) => {
                        const isForResidents = rec.toLowerCase().includes('residents');
                        const isForAuthorities = rec.toLowerCase().includes('authorities');
                        
                        return (
                          <div key={idx} className={`recommendation-item ${
                            isForResidents ? 'for-residents' : 
                            isForAuthorities ? 'for-authorities' : 'general'
                          }`}>
                            <div className="rec-icon">
                              {isForResidents ? '🏠' : isForAuthorities ? '🏛️' : '📋'}
                            </div>
                            <div className="rec-content">
                              <p>{rec.replace(/\*\*/g, '')}</p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )
                )}

                {/* Future Prediction */}
                {renderSection(
                  "🔮 Future Outlook",
                  parsedAnalysis.futurePrediction,
                  (prediction) => (
                    <div className="prediction-card">
                      <p>{prediction}</p>
                    </div>
                  )
                )}
              </>
            ) : analysis ? (
              /* Fallback to raw analysis if parsing fails */
              <div className="detailed-analysis">
                <h4>📊 Complete Analysis Report</h4>
                <div className="analysis-card">
                  <pre>{typeof analysis === 'object' ? JSON.stringify(analysis, null, 2) : analysis}</pre>
                </div>
              </div>
            ) : null}

            {/* Original FVI Key Factors for comparison */}
            {fvi.key_factors && fvi.key_factors.length > 0 && (
              <div className="fvi-factors">
                <h4>📈 FVI Analysis Factors</h4>
                <div className="fvi-factors-list">
                  {fvi.key_factors.map((factor, idx) => (
                    <div key={idx} className="fvi-factor-item">
                      • {factor}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="no-data">
            <div className="no-data-icon">🗺️</div>
            <h4>No Location Selected</h4>
            <p>Click on the map to select a location and view detailed flood risk analysis.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FVIDetailsPanel;