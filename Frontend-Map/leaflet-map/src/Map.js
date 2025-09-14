// // import React from 'react';
// // import { MapContainer, TileLayer, Marker, Popup, LayersControl } from 'react-leaflet';
// // import 'leaflet/dist/leaflet.css';
// // import L from 'leaflet';

// // // To fix the issue with marker icons
// // delete L.Icon.Default.prototype._getIconUrl;

// // L.Icon.Default.mergeOptions({
// //   iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
// //   iconUrl: require('leaflet/dist/images/marker-icon.png'),
// //   shadowUrl: require('leaflet/dist/images/marker-shadow.png')
// // });

// // const Map = () => {
// //   const position = [51.505, -0.09]; // latitude and longitude

// //   return (
// //     <MapContainer center={position} zoom={13} style={{ height: "100vh", width: "100%" }}>
// //       <TileLayer
// //         url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
// //         attribution='&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
// //       />
// //       <Marker position={position}>
// //         <Popup>
// //           A pretty CSS3 popup. <br /> Easily customizable.
// //         </Popup>
// //       </Marker>
// //     </MapContainer>
// //   );
// // }

// // export default Map;



// import React from 'react';
// import { MapContainer, TileLayer, LayersControl } from 'react-leaflet';
// import 'leaflet/dist/leaflet.css';

// const Map = () => {
//   const position = [51.505, -0.09]; // London coordinates, map will still center here

//   return (
//     <MapContainer center={position} zoom={13} style={{ height: "100vh", width: "100%" }}>
//       {/* The LayersControl component provides the UI for switching base layers */}
//       <LayersControl position="topright">
        
//         {/* Base Layer 1: OpenStreetMap */}
//         <LayersControl.BaseLayer checked name="Default View">
//           <TileLayer
//             url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
//             attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
//           />
//         </LayersControl.BaseLayer>
        
//         {/* Base Layer 2: A Dark Mode map from CartoDB */}
//         <LayersControl.BaseLayer name="Dark Mode">
//           <TileLayer
//             url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
//             attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
//           />
//         </LayersControl.BaseLayer>

//         {/* Base Layer 3: A Topographical map */}
//         <LayersControl.BaseLayer name="Topography">
//             <TileLayer
//                 url="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
//                 attribution='Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)'
//             />
//         </LayersControl.BaseLayer>

//       </LayersControl>
//     </MapContainer>
//   );
// }

// export default Map;


import React, { useState } from 'react';
import { MapContainer, TileLayer, LayersControl, Marker, Circle, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import './Map.css'; // Import the CSS file
import L from 'leaflet';
import RadiusControl from './RadiusControl'; // Import the menu component

// Fix for default marker icon issues with webpack
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});


// This component handles the map click events
function LocationFinder({ setPosition }) {
  useMapEvents({
    click(e) {
      // On click, update the position state in the parent component
      setPosition(e.latlng);
    },
  });
  return null; // This component doesn't render anything itself
}

const Map = () => {
  // Centered on your current location: Kandhauli, Uttarakhand
  const initialPosition = [29.9457, 78.1642]; 
  
  // State to hold the clicked position (initially null)
  const [position, setPosition] = useState(null);
  // State to hold the radius value
  const [radius, setRadius] = useState(1000); // Default radius of 1000 meters

  const circleOptions = { color: 'red', fillColor: 'red' };

  return (
    <>
      <RadiusControl radius={radius} setRadius={setRadius} />
      <MapContainer center={initialPosition} zoom={13} style={{ height: "100vh", width: "100%" }}>
        <LayersControl position="topright">
          {/* --- Base Layers --- */}
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

          {/* --- NEW MAP TYPES ADDED BELOW --- */}

          <LayersControl.BaseLayer name="Satellite View (Esri)">
            <TileLayer
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              attribution='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
            />
          </LayersControl.BaseLayer>

          <LayersControl.BaseLayer name="Light View (Stadia)">
            <TileLayer
              url="https://tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png"
              attribution='&copy; <a href="https://www.stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
          </LayersControl.BaseLayer>

          <LayersControl.BaseLayer name="Humanitarian View (HOT)">
            <TileLayer
              url="https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles style by <a href="https://www.hotosm.org/" target="_blank">Humanitarian OpenStreetMap Team</a> hosted by <a href="https://openstreetmap.fr/" target="_blank">OpenStreetMap France</a>'
            />
          </LayersControl.BaseLayer>

        </LayersControl>

        {/* This component listens for clicks */}
        <LocationFinder setPosition={setPosition} />

        {/* Conditionally render the marker and circle only if a position is set */}
        {position && (
          <>
            <Marker position={position}></Marker>
            <Circle center={position} pathOptions={circleOptions} radius={radius} />
          </>
        )}
      </MapContainer>
    </>
  );
};

export default Map;