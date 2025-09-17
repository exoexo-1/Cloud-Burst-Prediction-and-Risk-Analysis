import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, LayersControl, Marker, Circle, Tooltip, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './Map.css';
import L from 'leaflet';
import RadiusControl from './RadiusControl';
import FVIDetailsPanel from './FVIDetailsPanel';

// Fix for default marker icon issues with webpack
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

function LocationFinder({ setPosition }) {
  useMapEvents({
    click(e) {
      setPosition(e.latlng);
    },
  });
  return null;
}

const Map = ({ onNavigateHome }) => {
  const initialPosition = [29.9457, 78.1642]; 
  
  const [position, setPosition] = useState(null);
  const [radius, setRadius] = useState(1000);
  const [placeName, setPlaceName] = useState('');
  const [fvi, setFvi] = useState(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  const circleOptions = { color: 'red', fillColor: 'red' };

  // Reverse geocode for place name
  useEffect(() => {
    if (position) {
      setPlaceName("Fetching name...");
      const { lat, lng } = position;
      fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`)
        .then(response => response.json())
        .then(data => {
          if (data && data.display_name) {
            setPlaceName(data.display_name);
          } else {
            setPlaceName("Name not found");
          }
        })
        .catch(error => {
          console.error("Error fetching place name:", error);
          setPlaceName("Could not fetch name");
        });
    }
  }, [position]);

  useEffect(() => {
    if (position) {
      setFvi(null); // reset while fetching
      const { lat, lng } = position;

      fetch(`https://fuzzy-api-3e87.onrender.com/fvi?lat=${lat}&lon=${lng}`)
        .then(res => res.json())
        .then(data => {
          setFvi(data);
        })
        .catch(err => {
          console.error("Error fetching FVI:", err);
          setFvi({ fvi_score: "N/A", key_factors: ["Error fetching data"] });
        });
    }
  }, [position]);

  const togglePanel = () => {
    setIsPanelOpen(!isPanelOpen);
  };

  const closePanel = () => {
    setIsPanelOpen(false);
  };

  return (
    <div className="map-wrapper">
      <button className="back-to-home-btn" onClick={onNavigateHome}>
        &larr; Back to Home
      </button>

      <RadiusControl radius={radius} setRadius={setRadius} />
      
      <div className="fvi-button-container">
        <button
          className={`fvi-details-btn ${!fvi || isPanelOpen ? 'disabled' : ''}`}
          onClick={togglePanel}
          disabled={!fvi || isPanelOpen}
        >
          {!fvi ? 'Loading FVI...' : 'FVI Details'}
        </button>
      </div>
      
      <MapContainer center={initialPosition} zoom={13} style={{ height: "100vh", width: "100%" }}>
        <LayersControl position="topright">
          <LayersControl.BaseLayer checked name="Default View (OpenStreetMap)">
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="Dark Mode (CartoDB)">
            <TileLayer
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="Satellite View (Esri)">
            <TileLayer
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              attribution='Tiles &copy; Esri'
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="Light View (Stadia)">
            <TileLayer
              url="https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png"
              attribution='&copy; Stadia Maps, &copy; OpenMapTiles &copy; OpenStreetMap contributors'
            />
          </LayersControl.BaseLayer>
        </LayersControl>

        <LocationFinder setPosition={setPosition} />

        {position && (
          <>
            <Marker position={position}>
              <Tooltip permanent direction="right" offset={[10, 0]} className="custom-tooltip">
                <strong>Place Name:</strong> {placeName} <br />
                <strong>FVI Score:</strong>{" "}
                {fvi ? `${fvi.fvi_score}/100` : "Loading..."} <br />
                <strong>Key Factors:</strong>
                <ul style={{ margin: "5px 0", paddingLeft: "15px" }}>
                  {fvi && fvi.key_factors
                    ? fvi.key_factors.map((factor, idx) => (
                        <li key={idx}>{factor}</li>
                      ))
                    : <li>Loading...</li>}
                </ul>
              </Tooltip>
            </Marker>
            
            <Circle center={position} pathOptions={circleOptions} radius={radius} />
          </>
        )}
      </MapContainer>

      <FVIDetailsPanel 
        isOpen={isPanelOpen}
        onClose={closePanel}
        position={position}
        fvi={fvi}
        placeName={placeName}
      />
    </div>
  );
};

export default Map;