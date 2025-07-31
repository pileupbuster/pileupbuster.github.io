import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { formatLocationDisplay } from '../utils/addressFormatter';

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

interface QueueItem {
  callsign: string;
  name?: string;
  timeInQueue: number;
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

interface MapSectionProps {
  workedOperators: WorkedItem[];
  currentOperator: CurrentOperator | null;
  queueItems?: QueueItem[];
}

function MapSection({ workedOperators, currentOperator, queueItems = [] }: MapSectionProps) {
  const mapRef = useRef<L.Map | null>(null);
  const mapContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    // Initialize map with darker tiles using CartoDB Dark Matter (English-only labels)
    const map = L.map(mapContainerRef.current).setView([45, -93], 4);

    // Using CartoDB Dark Matter tiles which typically show English-only place names
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors © <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: 'abcd',
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

    // NOTE: Queue members should NOT appear on the map - only worked operators
    // Queue members are displayed in the QueueBar component instead
    
    // Add worked operators to map (people who completed QSOs)
    workedOperators.forEach(operator => {
      if (operator.grid?.lat && operator.grid?.long) {
        const icon = L.divIcon({
          html: operator.image 
            ? `<div class="marker-avatar worked"><img src="${operator.image}" alt="${operator.callsign}" /></div>`
            : `<div class="marker-avatar worked placeholder">👤</div>`,
          iconSize: [60, 60],  // Back to 60x60 for optimal visibility
          iconAnchor: [30, 30],  // Adjusted anchor point (half of iconSize)
          popupAnchor: [0, -30],  // Adjusted popup anchor
          className: 'custom-marker'
        });

        const marker = L.marker([operator.grid.lat, operator.grid.long], { icon })
          .addTo(mapRef.current!);
        
        marker.bindPopup(`
          <div class="map-popup">
            <strong>${operator.callsign}</strong><br>
            ${operator.name || operator.callsign}<br>
            ${formatLocationDisplay(operator.address, operator.dxcc_name)}<br>
            <span style="color: #4CAF50;">✅ QSO Completed</span><br>
            <a href="https://www.qrz.com/db/${operator.callsign}" target="_blank" style="color: #4a9eff;">View Profile</a>
          </div>
        `);
        
        // Remove the automatic QRZ page opening - let users click the link in the popup instead
      }
    });

    // Note: Current operator should NOT appear on the map until QSO is completed
    // The map shows ONLY worked operators (completed QSOs) - persistent with 24h TTL
    // Queue members are displayed in the QueueBar component
    // Current operator is displayed in the CurrentActiveCallsign component
  }, [workedOperators, currentOperator, queueItems]);

  return (
    <div className="map-section">
      <div ref={mapContainerRef} className="map-container"></div>
    </div>
  );
}

export default MapSection;
