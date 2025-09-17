import React, { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

// Manages the lightning flash effect
function Lightning() {
  const ref = useRef();

  // Animation loop for the lightning
  useFrame(() => {
    if (ref.current) {
      // Randomly trigger a new flash
      if (Math.random() > 0.98) {
        // Set a very high power for a bright flash
        ref.current.power = 50 + Math.random() * 3500;
        // Reposition the light for each flash
        ref.current.position.set(
          Math.random() * 400 - 200,
          300 + Math.random() * 200,
          100
        );
      } else if (ref.current.power > 0) {
        // If not flashing, decay the light's power quickly to create a flicker effect
        ref.current.power -= 100;
      }
    }
  });
  return (
    <pointLight
      ref={ref}
      color={0x00bfff} // A brighter, "Deep Sky Blue" color
      distance={500}
      decay={1.7}
      power={0} // Start with no power
    />
  );
}

// Manages the animated rain particles
function Rain() {
  const ref = useRef();
  const rainCount = 15000;

  const rainGeo = useMemo(() => {
    const geometry = new THREE.BufferGeometry();
    const vertices = [];
    for (let i = 0; i < rainCount; i++) {
      vertices.push(
        Math.random() * 400 - 200,
        Math.random() * 500 - 250,
        Math.random() * 400 - 200
      );
    }
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    return geometry;
  }, [rainCount]);

  useFrame(() => {
    if (ref.current) {
      const positions = rainGeo.attributes.position.array;
      for (let i = 0; i < positions.length; i += 3) {
        // Increased speed for a more dramatic downpour
        positions[i + 1] -= 1.2 + Math.random() * 0.3;
        if (positions[i + 1] < -200) {
          positions[i + 1] = 200;
        }
      }
      rainGeo.attributes.position.needsUpdate = true;
      ref.current.rotation.y += 0.002;
    }
  });

  return (
    <points ref={ref} geometry={rainGeo}>
      <pointsMaterial color={0xaaaaaa} size={0.18} transparent />
    </points>
  );
}

// Manages the rotating cloud planes
function Clouds() {
  const ref = useRef();
  const texture = useMemo(() => new THREE.TextureLoader().load('/smoke.png'), []);

  useFrame(() => {
    if (ref.current) {
      ref.current.children.forEach(cloud => {
        cloud.rotation.z -= 0.002;
      });
    }
  });

  return (
    <group ref={ref}>
      {Array.from({ length: 25 }).map((_, i) => (
        <mesh
          key={i}
          position={[
            Math.random() * 800 - 400,
            500,
            Math.random() * 500 - 500,
          ]}
          rotation={[1.16, -0.12, Math.random() * 2 * Math.PI]}
        >
          <planeGeometry args={[500, 500]} />
          <meshLambertMaterial map={texture} transparent opacity={0.35} />
        </mesh>
      ))}
    </group>
  );
}

// The main canvas component that holds the entire scene
const RainyScene = () => {
  return (
    <div style={{ 
        position: 'absolute', 
        top: 0, 
        left: 0, 
        width: '100%', 
        height: '100%', 
        zIndex: 0,
        pointerEvents: 'none'
    }}>
      <Canvas
        camera={{ fov: 60, position: [0, 0, 1], rotation: [1.16, -0.12, 0.27] }}
      >
        <fog attach="fog" args={[0x1c1c2a, 0.002]} />
        <ambientLight color={0x555555} />
        <directionalLight color={0xffeedd} position={[0, 0, 1]} />
        <Lightning />
        <Rain />
        <Clouds />
      </Canvas>
    </div>
  );
};

export default RainyScene;