import React, { useEffect, useState } from 'react';
import './FVIDetailsPanel.css';

const FVIDetailsPanel = ({ isOpen, onClose, position, fvi, placeName }) => {
  const [analysis, setAnalysis] = useState(null);
  const [parsedAnalysis, setParsedAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Enhanced flexible parser for structured AI response
  const parseAnalysis = (rawAnalysis) => {
    if (!rawAnalysis) return null;

    console.log("Raw analysis data:", rawAnalysis);

    const analysisText = typeof rawAnalysis === 'object'
      ? JSON.stringify(rawAnalysis, null, 2)
      : rawAnalysis;

    console.log("Analysis text to parse:", analysisText);

    const sections = {};
    const lines = analysisText.split('\n');
    let currentSection = null;
    let content = [];

    // Enhanced regex patterns to match various formats
    const sectionPatterns = {
      floodRisk: /(?:#{1,6}\s*)?(?:\d+\.\s*)?(?:\*\*)?flood risk level(?:\*\*)?:?\s*/i,
      cloudburstProb: /(?:#{1,6}\s*)?(?:\d+\.\s*)?(?:\*\*)?cloudburst probability(?:\*\*)?:?\s*/i,
      keyFactors: /(?:#{1,6}\s*)?(?:\d+\.\s*)?(?:\*\*)?key (?:risk\s+)?factors?(?:\*\*)?:?\s*/i,
      historicalContext: /(?:#{1,6}\s*)?(?:\d+\.\s*)?(?:\*\*)?historical?(?:\/geographical)?\s*(?:&\s*geographical)?\s*context(?:\*\*)?:?\s*/i,
      recommendations: /(?:#{1,6}\s*)?(?:\d+\.\s*)?(?:\*\*)?recommendations(?:\*\*)?:?\s*/i,
      futurePrediction: /(?:#{1,6}\s*)?(?:\d+\.\s*)?(?:\*\*)?future.*(?:prediction|report|outlook)(?:\*\*)?:?\s*/i,
      monitoringRecommendations: /(?:\*\*)?monitoring recommendations(?:\*\*)?:?\s*/i
    };

    for (let line of lines) {
      const originalLine = line;
      line = line.trim();
      if (!line) continue;

      console.log("Processing line:", line);

      // Section header detection
      let sectionFound = false;
      for (const [sectionKey, pattern] of Object.entries(sectionPatterns)) {
        if (pattern.test(line)) {
          console.log(`Found section: ${sectionKey} in line: ${line}`);
          
          // Save previous section content
          if (currentSection && content.length > 0) {
            sections[currentSection] = processSectionContent(currentSection, content);
            console.log(`Saved section ${currentSection}:`, sections[currentSection]);
          }

          // Initialize new section
          currentSection = sectionKey;
          content = [];
          
          // Check if the section value is on the same line
          const valueMatch = line.match(pattern);
          if (valueMatch && valueMatch.index !== undefined) {
            const remainingText = line.substring(valueMatch.index + valueMatch[0].length).trim();
            if (remainingText) {
              content.push(remainingText);
            }
          }
          
          sectionFound = true;
          break;
        }
      }

      if (sectionFound) continue;

      // Handle reasoning lines specifically
      if (line.match(/^\*reasoning:\*/i) || line.match(/^\*.*reasoning.*\*/i)) {
        const reasoningText = line.replace(/^\*reasoning:\*/i, '').replace(/^\*.*reasoning.*\*/i, '').trim();
        if (currentSection === 'cloudburstProb' && sections[currentSection] && typeof sections[currentSection] === 'object') {
          sections[currentSection].reasoning = reasoningText;
        } else {
          content.push({ type: 'reasoning', text: reasoningText });
        }
        continue;
      }

      // Handle subsection headers (For Residents, For Authorities, etc.)
      if (line.match(/^\*\*(?:for\s+)?(?:residents|authorities|monitoring recommendations)(?:\*\*)?:?\s*/i)) {
        const subsectionType = line.toLowerCase().includes('resident') ? 'residents' :
                              line.toLowerCase().includes('authorities') ? 'authorities' :
                              line.toLowerCase().includes('monitoring') ? 'monitoring' : 'general';
        content.push({ type: 'subsection', category: subsectionType, text: line.replace(/\*\*/g, '').replace(/:/g, '').trim() });
        continue;
      }

      // Handle bullet points and regular content
      if (currentSection && line) {
        if (line.startsWith('-') || line.startsWith('•') || line.startsWith('*')) {
          const bulletText = line.replace(/^[-•*]\s*/, '').trim();
          if (bulletText.startsWith('**') && bulletText.includes('**')) {
            const [boldPart, ...rest] = bulletText.split('**');
            content.push({ type: 'bullet', bold: boldPart.replace(/\*\*/g, ''), text: rest.join('**').replace(/^:\s*/, '') });
          } else {
            content.push({ type: 'bullet', text: bulletText });
          }
        } else {
          content.push({ type: 'text', text: line });
        }
      }
    }

    // Save the last section
    if (currentSection && content.length > 0) {
      sections[currentSection] = processSectionContent(currentSection, content);
      console.log(`Final section ${currentSection}:`, sections[currentSection]);
    }

    console.log("Final parsed sections:", sections);
    return sections;
  };

  // Process content based on section type
  const processSectionContent = (sectionKey, content) => {
    if (sectionKey === 'floodRisk') {
      return content.length > 0 ? content[0].text || content[0] : '';
    }
    
    if (sectionKey === 'cloudburstProb') {
      const result = { value: '', reasoning: '' };
      let processingReasoning = false;
      
      content.forEach(item => {
        if (typeof item === 'object' && item.type === 'reasoning') {
          result.reasoning = item.text;
        } else if (typeof item === 'string' || (typeof item === 'object' && item.text)) {
          const text = typeof item === 'string' ? item : item.text;
          if (!result.value && !text.toLowerCase().includes('reasoning')) {
            result.value = text;
          } else if (text.toLowerCase().includes('reasoning') || processingReasoning) {
            processingReasoning = true;
            result.reasoning += (result.reasoning ? ' ' : '') + text.replace(/reasoning:\s*/i, '');
          }
        }
      });
      
      return result;
    }

    if (sectionKey === 'keyFactors' || sectionKey === 'recommendations') {
      return content.map(item => {
        if (typeof item === 'object') {
          if (item.type === 'bullet') {
            return {
              text: item.text,
              bold: item.bold,
              type: 'bullet'
            };
          } else if (item.type === 'subsection') {
            return {
              text: item.text,
              category: item.category,
              type: 'subsection'
            };
          }
          return item;
        }
        return { text: item, type: 'text' };
      });
    }

    // For other sections, join text content
    return content.map(item => {
      if (typeof item === 'object' && item.text) {
        return item.text;
      }
      return typeof item === 'string' ? item : '';
    }).filter(Boolean).join(' ');
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

      console.log("Fetching analysis for:", requestBody);

      fetch(`https://cloud-burst-prediction-and-risk-analysis-69by.onrender.com/analysis`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify(requestBody),
      })
      .then(res => {
        console.log("Response status:", res.status);
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        return res.json();
      })
      .then(data => {
        console.log("Response data:", data);
        if (data.status === "error") {
          setError(data.error || "Unknown error occurred");
        } else {
          const rawAnalysis = data.analysis || "No analysis available.";
          console.log("Raw analysis received:", rawAnalysis);
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

  const getCloudburstIcon = (value) => {
    if (!value) return '⚪';
    const lowerValue = value.toLowerCase();
    if (lowerValue.includes('yes') || lowerValue.includes('high')) return '⛈️';
    if (lowerValue.includes('no') || lowerValue.includes('low')) return '🌤️';
    if (lowerValue.includes('moderate')) return '⛅';
    return '❓';
  };

  const getCloudburstColor = (value) => {
    if (!value) return '#6c757d';
    const lowerValue = value.toLowerCase();
    if (lowerValue.includes('yes') || lowerValue.includes('high')) return '#dc3545';
    if (lowerValue.includes('no') || lowerValue.includes('low')) return '#28a745';
    if (lowerValue.includes('moderate')) return '#ffc107';
    return '#6c757d';
  };

  const renderSection = (title, content, renderFunction) => {
    if (!content) return null;
    return (
      <div className="analysis-section">
        <h4>{title}</h4>
        {renderFunction(content)}
      </div>
    );
  };

  const renderFactorsOrRecommendations = (items, isRecommendations = false) => {
    if (!Array.isArray(items)) return null;

    let currentSubsection = null;
    const groupedItems = [];
    let currentGroup = [];

    items.forEach(item => {
      if (item.type === 'subsection') {
        if (currentGroup.length > 0) {
          groupedItems.push({ category: currentSubsection, items: currentGroup });
          currentGroup = [];
        }
        currentSubsection = item.category;
        groupedItems.push({ type: 'subsection', text: item.text, category: item.category });
      } else {
        currentGroup.push(item);
      }
    });

    if (currentGroup.length > 0) {
      groupedItems.push({ category: currentSubsection, items: currentGroup });
    }

    return (
      <div className={isRecommendations ? "recommendations-container" : "factors-container"}>
        {groupedItems.map((group, idx) => {
          if (group.type === 'subsection') {
            return (
              <div key={idx} className="subsection-header">
                <div className="subsection-icon">
                  {group.category === 'residents' ? '👥' : 
                   group.category === 'authorities' ? '🏛️' : 
                   group.category === 'monitoring' ? '📊' : '📋'}
                </div>
                <h5>{group.text}</h5>
              </div>
            );
          }

          const categoryClass = group.category || 'general';
          return (
            <div key={idx} className={`items-group ${categoryClass}`}>
              {group.items.map((item, itemIdx) => (
                <div key={itemIdx} className={`item-card ${isRecommendations ? 'recommendation-item' : 'factor-item'}`}>
                  <div className="item-bullet">
                    {isRecommendations ? 
                      (group.category === 'residents' ? '🏠' : 
                       group.category === 'authorities' ? '🏛️' : 
                       group.category === 'monitoring' ? '📊' : '💡') : '•'}
                  </div>
                  <div className="item-content">
                    {item.bold && (
                      <strong className="item-header">{item.bold}:</strong>
                    )}
                    <span className="item-text">{item.text}</span>
                  </div>
                </div>
              ))}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className={`fvi-details-panel ${isOpen ? 'open' : ''}`}>
      <div className="fvi-panel-header">
        <div className="header-content">
          <h3>🌧️ Flood Risk Analysis Report</h3>
          <p className="header-subtitle">AI-Powered Risk Assessment</p>
        </div>
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
            <button className="retry-btn" onClick={() => setError(null)}>Retry Analysis</button>
          </div>
        ) : position && fvi ? (
          <>
            {/* Location Info Card */}
            <div className="location-info-card">
              <div className="location-header">
                <h4>📍 Location Overview</h4>
                <div className="fvi-badge">
                  FVI Score: <span className="fvi-score">{fvi.fvi_score}/100</span>
                </div>
              </div>
              <div className="location-details">
                <div className="location-item">
                  <span className="label">Place:</span>
                  <span className="value">{placeName}</span>
                </div>
                <div className="location-item">
                  <span className="label">Coordinates:</span>
                  <span className="value">{position.lat.toFixed(4)}, {position.lng.toFixed(4)}</span>
                </div>
                <div className="location-item">
                  <span className="label">Risk Level:</span>
                  <span className="value risk-level" style={{ color: getRiskLevelColor(fvi.risk_level) }}>
                    {fvi.risk_level}
                  </span>
                </div>
              </div>
            </div>

            {/* AI Analysis Results */}
            {loading ? (
              <div className="loading-section">
                <div className="loading-header">
                  <h4>🤖 AI Analysis in Progress</h4>
                  <p>Analyzing meteorological conditions and risk factors...</p>
                </div>
                <div className="loading-animation">
                  <div className="loading-spinner"></div>
                  <div className="loading-steps">
                    <div className="step active">Processing location data</div>
                    <div className="step active">Analyzing weather patterns</div>
                    <div className="step">Generating risk assessment</div>
                  </div>
                </div>
              </div>
            ) : parsedAnalysis ? (
              <>
                {/* Enhanced Risk Assessment Summary */}
                {(parsedAnalysis.floodRisk || parsedAnalysis.cloudburstProb) && (
                  <div className="risk-assessment-card">
                    <h4>⚡ AI Risk Assessment</h4>
                    <div className="risk-metrics">
                      {parsedAnalysis.floodRisk && (
                        <div className="metric-card flood-risk">
                          <div className="metric-header">
                            <div className="metric-icon">{getRiskIcon(parsedAnalysis.floodRisk)}</div>
                            <div className="metric-info">
                              <span className="metric-label">Flood Risk Level</span>
                              <span 
                                className="metric-value" 
                                style={{ color: getRiskLevelColor(parsedAnalysis.floodRisk) }}
                              >
                                {parsedAnalysis.floodRisk}
                              </span>
                            </div>
                          </div>
                        </div>
                      )}

                      {parsedAnalysis.cloudburstProb && (
                        <div className="metric-card cloudburst-risk">
                          <div className="metric-header">
                            <div className="metric-icon">
                              {getCloudburstIcon(parsedAnalysis.cloudburstProb.value)}
                            </div>
                            <div className="metric-info">
                              <span className="metric-label">Cloudburst Probability</span>
                              <span 
                                className="metric-value"
                                style={{ color: getCloudburstColor(parsedAnalysis.cloudburstProb.value) }}
                              >
                                {parsedAnalysis.cloudburstProb.value || 'Unknown'}
                              </span>
                            </div>
                          </div>
                          {parsedAnalysis.cloudburstProb.reasoning && (
                            <div className="metric-reasoning">
                              <strong>Analysis:</strong> {parsedAnalysis.cloudburstProb.reasoning}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Enhanced Key Factors */}
                {renderSection(
                  "🔑 Key Risk Factors",
                  parsedAnalysis.keyFactors,
                  (factors) => renderFactorsOrRecommendations(factors, false)
                )}

                {/* Enhanced Historical Context */}
                {renderSection(
                  "🏛️ Historical & Geographical Context",
                  parsedAnalysis.historicalContext,
                  (context) => (
                    <div className="context-card">
                      <div className="context-content">
                        <p>{context}</p>
                      </div>
                    </div>
                  )
                )}

                {/* Enhanced Recommendations */}
                {renderSection(
                  "💡 Recommendations & Actions",
                  parsedAnalysis.recommendations,
                  (recommendations) => renderFactorsOrRecommendations(recommendations, true)
                )}

                {/* Enhanced Future Prediction */}
                {renderSection(
                  "🔮 Future Outlook & Monitoring",
                  parsedAnalysis.futurePrediction,
                  (prediction) => (
                    <div className="prediction-card">
                      <div className="prediction-content">
                        <p>{prediction}</p>
                      </div>
                      <div className="prediction-footer">
                        <span className="timestamp">
                          📅 Report generated: {new Date().toLocaleString()}
                        </span>
                      </div>
                    </div>
                  )
                )}

                {/* Monitoring Recommendations if available */}
                {parsedAnalysis.monitoringRecommendations && renderSection(
                  "📊 Monitoring Guidelines",
                  parsedAnalysis.monitoringRecommendations,
                  (monitoring) => (
                    <div className="monitoring-card">
                      <div className="monitoring-content">
                        <p>{monitoring}</p>
                      </div>
                    </div>
                  )
                )}
              </>
            ) : analysis ? (
              <div className="fallback-analysis">
                <h4>📊 Raw Analysis Data</h4>
                <div className="raw-analysis-card">
                  <pre>{typeof analysis === 'object' ? JSON.stringify(analysis, null, 2) : analysis}</pre>
                </div>
              </div>
            ) : null}

            {/* Original FVI Data Reference */}
            {fvi.key_factors && fvi.key_factors.length > 0 && (
              <div className="fvi-reference">
                <h4>📈 FVI Model Factors</h4>
                <div className="fvi-factors-grid">
                  {fvi.key_factors.map((factor, idx) => (
                    <div key={idx} className="fvi-factor-card">
                      <span className="factor-index">{idx + 1}</span>
                      <span className="factor-description">{factor}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="no-data-state">
            <div className="no-data-icon">🗺️</div>
            <h4>Select Location for Analysis</h4>
            <p>Click anywhere on the map to get detailed flood risk analysis powered by AI</p>
            <div className="feature-highlights">
              <div className="feature">🤖 AI-powered risk assessment</div>
              <div className="feature">📊 Real-time data analysis</div>
              <div className="feature">💡 Actionable recommendations</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FVIDetailsPanel;