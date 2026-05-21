import { useMemo, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Billboard, Html, Line, OrbitControls, Stars } from '@react-three/drei'
import * as THREE from 'three'
import { useNeoStore } from '../store/neoStore'

const TIER_COLOR = {
  LOW: '#22c55e',
  MEDIUM: '#eab308',
  HIGH: '#f97316',
  CRITICAL: '#ef4444',
}

const PLANETS = [
  { name: 'Mercury', orbit: 0.39, radius: 0.018, period: 88, color: '#b8aa95', emissive: '#3b322a', speed: 1.9, phase: 0.4 },
  { name: 'Venus', orbit: 0.72, radius: 0.034, period: 225, color: '#e6be7a', emissive: '#5a3c16', speed: 1.45, phase: 1.7 },
  { name: 'Earth', orbit: 1.0, radius: 0.038, period: 365.25, color: '#2f7dff', emissive: '#002f9a', speed: 1.25, phase: 2.6 },
  { name: 'Mars', orbit: 1.52, radius: 0.026, period: 687, color: '#d95f3d', emissive: '#5a180d', speed: 1.05, phase: 3.4 },
  { name: 'Jupiter', orbit: 5.2, radius: 0.088, period: 4333, color: '#d8b48b', emissive: '#4b2d17', speed: 0.65, phase: 4.1 },
  { name: 'Saturn', orbit: 9.58, radius: 0.078, period: 10759, color: '#dbc383', emissive: '#4b3c16', speed: 0.52, phase: 5.0, rings: true },
  { name: 'Uranus', orbit: 19.2, radius: 0.056, period: 30687, color: '#83d8e8', emissive: '#134d58', speed: 0.42, phase: 5.7 },
  { name: 'Neptune', orbit: 30.05, radius: 0.054, period: 60190, color: '#476dff', emissive: '#10226e', speed: 0.36, phase: 0.9 },
]

function sceneRadius(au) {
  return Math.sqrt(au) * 1.18
}

function orbitPoints(radius, segments = 192) {
  const points = []
  for (let i = 0; i <= segments; i += 1) {
    const angle = (i / segments) * Math.PI * 2
    points.push(new THREE.Vector3(Math.cos(angle) * radius, 0, Math.sin(angle) * radius))
  }
  return points
}

function Sun() {
  const sunRef = useRef()
  const coronaRef = useRef()

  useFrame(({ clock }) => {
    const elapsed = clock.getElapsedTime()
    if (sunRef.current) sunRef.current.rotation.y = elapsed * 0.08
    if (coronaRef.current) {
      const pulse = 1 + Math.sin(elapsed * 1.8) * 0.04
      coronaRef.current.scale.setScalar(pulse)
    }
  })

  return (
    <group>
      <mesh ref={coronaRef}>
        <sphereGeometry args={[0.32, 48, 48]} />
        <meshBasicMaterial color="#ffb02e" transparent opacity={0.12} depthWrite={false} />
      </mesh>
      <mesh ref={sunRef}>
        <sphereGeometry args={[0.16, 48, 48]} />
        <meshStandardMaterial emissive="#ff9f1a" emissiveIntensity={4.5} color="#ffe27a" roughness={0.32} />
      </mesh>
      <pointLight intensity={4.8} distance={40} color="#fff2c2" />
    </group>
  )
}

function PlanetOrbit({ planet }) {
  const radius = sceneRadius(planet.orbit)
  const points = useMemo(() => orbitPoints(radius), [radius])
  const opacity = planet.orbit <= 1.6 ? 0.46 : 0.26

  return (
    <Line
      points={points}
      color={planet.color}
      lineWidth={planet.name === 'Earth' ? 1.1 : 0.55}
      transparent
      opacity={opacity}
    />
  )
}

function Planet({ planet, day }) {
  const groupRef = useRef()
  const meshRef = useRef()
  const radius = sceneRadius(planet.orbit)

  useFrame(({ clock }) => {
    const elapsed = clock.getElapsedTime()
    const acceleratedDay = day + elapsed * 18 * planet.speed
    const angle = planet.phase + (acceleratedDay / planet.period) * Math.PI * 2
    const y = Math.sin(angle * 1.7 + planet.phase) * 0.015

    if (groupRef.current) {
      groupRef.current.position.set(Math.cos(angle) * radius, y, Math.sin(angle) * radius)
    }
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.006 + planet.speed * 0.002
      meshRef.current.rotation.z = planet.name === 'Uranus' ? 1.55 : 0.18
    }
  })

  return (
    <group ref={groupRef}>
      <mesh ref={meshRef}>
        <sphereGeometry args={[planet.radius, 32, 32]} />
        <meshStandardMaterial
          color={planet.color}
          emissive={planet.emissive}
          emissiveIntensity={0.55}
          metalness={0.05}
          roughness={0.48}
        />
      </mesh>

      {planet.name === 'Earth' && (
        <mesh position={[planet.radius * 1.9, planet.radius * 0.2, 0]}>
          <sphereGeometry args={[0.009, 12, 12]} />
          <meshStandardMaterial color="#d9e7ff" emissive="#9ab8ff" emissiveIntensity={0.8} />
        </mesh>
      )}

      {planet.rings && (
        <mesh rotation={[Math.PI / 2.5, 0.25, 0]}>
          <ringGeometry args={[planet.radius * 1.45, planet.radius * 2.35, 72]} />
          <meshBasicMaterial color="#d8c58c" transparent opacity={0.62} side={THREE.DoubleSide} />
        </mesh>
      )}

      <Billboard follow lockX={false} lockY={false} lockZ={false}>
        <Html center distanceFactor={9} style={{ pointerEvents: 'none' }}>
          <div className="planet-label" style={{ color: planet.color }}>
            {planet.name}
          </div>
        </Html>
      </Billboard>
    </group>
  )
}

function AsteroidBelt() {
  const particles = useMemo(() => {
    return Array.from({ length: 180 }, (_, i) => {
      const t = (i / 180) * Math.PI * 2
      const jitter = Math.sin(i * 9.17) * 0.11 + Math.cos(i * 3.31) * 0.06
      const radius = sceneRadius(2.55 + jitter)
      return [Math.cos(t) * radius, Math.sin(i * 1.7) * 0.025, Math.sin(t) * radius]
    })
  }, [])

  return (
    <group>
      {particles.map((position, index) => (
        <mesh key={index} position={position}>
          <sphereGeometry args={[0.004, 6, 6]} />
          <meshBasicMaterial color="#7f8798" transparent opacity={0.45} />
        </mesh>
      ))}
    </group>
  )
}

function NEOOrbit({ neo, orbitData, isSelected, day, onClick }) {
  const color = TIER_COLOR[neo.risk_tier] || '#4f9eff'

  if (!orbitData?.path?.length) return null

  const points = orbitData.path.map(p => {
    const scale = sceneRadius(Math.max(0.08, Math.sqrt(p.x * p.x + p.y * p.y + p.z * p.z)))
    const direction = new THREE.Vector3(p.x, p.z * 0.55, p.y)
    if (direction.length() === 0) return new THREE.Vector3()
    return direction.normalize().multiplyScalar(scale)
  })

  const idx = Math.min(Math.floor((day / 30) * (points.length - 1)), points.length - 1)
  const pos = points[idx]

  return (
    <group>
      <Line
        points={points}
        color={color}
        lineWidth={isSelected ? 2.8 : 1.1}
        transparent
        opacity={isSelected ? 0.95 : 0.42}
        onClick={onClick}
      />
      {pos && (
        <group position={[pos.x, pos.y, pos.z]}>
          <mesh onClick={onClick}>
            <sphereGeometry args={[isSelected ? 0.028 : 0.019, 14, 14]} />
            <meshStandardMaterial color={color} emissive={color} emissiveIntensity={isSelected ? 2.4 : 1.25} />
          </mesh>
          {isSelected && (
            <Billboard>
              <Html center distanceFactor={8} style={{ pointerEvents: 'none' }}>
                <div className="neo-label" style={{ color, borderColor: `${color}66` }}>
                  {neo.name}
                </div>
              </Html>
            </Billboard>
          )}
        </group>
      )}
    </group>
  )
}

function SceneContent({ orbitDataMap }) {
  const { neos, selectedNeo, setSelectedNeo, scrubDay } = useNeoStore()

  return (
    <>
      <color attach="background" args={['#02040b']} />
      <fog attach="fog" args={['#02040b', 5.5, 13]} />
      <ambientLight intensity={0.2} />
      <hemisphereLight intensity={0.35} color="#5c8cff" groundColor="#15070a" />
      <Stars radius={95} depth={60} count={6200} factor={3.7} fade speed={0.28} />
      <Sun />
      {PLANETS.map(planet => <PlanetOrbit key={`${planet.name}-orbit`} planet={planet} />)}
      <AsteroidBelt />
      {PLANETS.map(planet => <Planet key={planet.name} planet={planet} day={scrubDay} />)}
      {neos.slice(0, 10).map(neo => (
        <NEOOrbit
          key={neo.id}
          neo={neo}
          orbitData={orbitDataMap[neo.id]}
          isSelected={selectedNeo?.id === neo.id}
          day={scrubDay}
          onClick={() => setSelectedNeo(neo)}
        />
      ))}
      <OrbitControls
        enablePan
        enableZoom
        enableRotate
        minDistance={1.4}
        maxDistance={13}
        dampingFactor={0.08}
        target={[0, 0, 0]}
        enableDamping
      />
    </>
  )
}

export function OrbitalScene({ orbitDataMap = {} }) {
  return (
    <Canvas
      camera={{ position: [0, 4.8, 7.2], fov: 48, near: 0.01, far: 120 }}
      gl={{ antialias: true, alpha: false, powerPreference: 'high-performance' }}
      dpr={[1, 1.7]}
      style={{ background: '#02040b' }}
    >
      <SceneContent orbitDataMap={orbitDataMap} />
    </Canvas>
  )
}
