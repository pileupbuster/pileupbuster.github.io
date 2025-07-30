import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

interface WorkedItem {
  callsign: string;
  name?: string;
  completedAt: string;
  source: 'pileupbuster' | 'direct';
  address?: string;
  grid?: {
    lat?: number;
    long?: number;
    grid?: string;
  };
  image?: string;
  dxcc_name?: string;
  location?: string;
}

interface CurrentOperator {
  callsign: string;
  name: string;
  location: string;
  coordinates: { lat: number; lon: number };
  profileImage: string;
}

interface MapSectionProps {
  workedOperators: WorkedItem[];
  currentOperator: CurrentOperator | null;
}

function MapSection({ workedOperators, currentOperator }: MapSectionProps) {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    // Initialize map with darker tiles using Stadia Maps
    const map = L.map(mapContainerRef.current).setView([45, -93], 4);

    // Using Stadia Maps Alidade Smooth Dark (matching the sample)
    // Note: The API key from the sample is embedded, but we'll use it as-is for now
    L.tileLayer('https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png?api_key=21ff9858-9e51-49fb-91eb-e587a86105e9', {
      attribution: '© <a href="https://www.stadiamaps.com/" target="_blank">Stadia Maps</a> © <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 20
    }).addTo(map);

    mapRef.current = map;

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!mapRef.current) return;

    // Clear existing markers
    mapRef.current.eachLayer((layer) => {
      if (layer instanceof L.Marker) {
        mapRef.current!.removeLayer(layer);
      }
    });

    // Add worked operators to map
    workedOperators.forEach(operator => {
      if (operator.grid?.lat && operator.grid?.long) {
        const icon = L.divIcon({
          html: operator.image 
            ? `<div class="marker-avatar worked"><img src="${operator.image}" alt="${operator.callsign}" /></div>`
            : `<div class="marker-avatar worked placeholder">👤</div>`,
          iconSize: [60, 60],
          iconAnchor: [30, 30],
          popupAnchor: [0, -30],
          className: 'custom-marker'
        });

        L.marker([operator.grid.lat, operator.grid.long], { icon })
          .addTo(mapRef.current!)
          .bindPopup(`
            <div class="map-popup">
              <strong>${operator.callsign}</strong><br>
              ${operator.name || operator.callsign}<br>
              ${operator.location || operator.address || operator.dxcc_name || 'Unknown'}
            </div>
          `);
      }
    });

    // Add current operator if exists
    if (currentOperator) {
      const icon = L.divIcon({
        html: currentOperator.profileImage 
          ? `<div class="marker-avatar current"><img src="${currentOperator.profileImage}" alt="${currentOperator.callsign}" /></div>`
          : `<div class="marker-avatar current placeholder">👤</div>`,
        iconSize: [60, 60],
        iconAnchor: [30, 30],
        popupAnchor: [0, -30],
        className: 'custom-marker'
      });

      L.marker([currentOperator.coordinates.lat, currentOperator.coordinates.lon], { icon })
        .addTo(mapRef.current!)
        .bindPopup(`
          <div class="map-popup">
            <strong>${currentOperator.callsign}</strong><br>
            ${currentOperator.name}<br>
            ${currentOperator.location}
          </div>
        `);
    }
  }, [workedOperators, currentOperator]);

  return (
    <div className="map-section">
      <div ref={mapContainerRef} className="map-container"></div>
    </div>
  );
}

export default MapSection;
