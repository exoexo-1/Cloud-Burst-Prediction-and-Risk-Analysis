import React from 'react';

// This component is the menu on the right.
// It receives the current radius and a function to update it.
const RadiusControl = ({ radius, setRadius }) => {
  return (
    <div className="radius-control-container">
      <h4>Set Radius</h4>
      <label htmlFor="radius">Radius (in meters):</label>
      <input
        type="number"
        id="radius"
        value={radius}
        onChange={(e) => setRadius(Number(e.target.value))}
        min="0"
      />
    </div>
  );
};

export default RadiusControl;