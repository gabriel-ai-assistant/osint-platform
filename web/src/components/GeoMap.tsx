import { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import type { GeoLocation } from '../types';
import 'leaflet/dist/leaflet.css';

// Fix default marker icon issue with bundlers
const defaultIcon = L.divIcon({
  html: `<div style="width:12px;height:12px;background:#00d4ff;border:2px solid #0a0e1a;border-radius:50%;box-shadow:0 0 8px #00d4ff;"></div>`,
  className: '',
  iconSize: [12, 12],
  iconAnchor: [6, 6],
});

interface Props {
  locations: GeoLocation[];
}

function FitBounds({ locations }: { locations: GeoLocation[] }) {
  const map = useMap();

  useEffect(() => {
    const validLocs = locations.filter(
      (l) => l.latitude != null && l.longitude != null
    );
    if (validLocs.length === 0) return;

    if (validLocs.length === 1) {
      map.setView([validLocs[0].latitude!, validLocs[0].longitude!], 6);
    } else {
      const bounds = L.latLngBounds(
        validLocs.map((l) => [l.latitude!, l.longitude!] as L.LatLngTuple)
      );
      map.fitBounds(bounds, { padding: [30, 30] });
    }
  }, [locations, map]);

  return null;
}

export default function GeoMap({ locations }: Props) {
  const validLocs = locations.filter(
    (l) => l.latitude != null && l.longitude != null
  );

  if (validLocs.length === 0) {
    return (
      <div className="h-64 bg-navy-700 rounded-lg flex items-center justify-center text-gray-500 text-sm">
        No geolocation data available
      </div>
    );
  }

  const center: [number, number] = [
    validLocs[0].latitude!,
    validLocs[0].longitude!,
  ];

  return (
    <div className="h-64 rounded-lg overflow-hidden border border-navy-600">
      <MapContainer
        center={center}
        zoom={4}
        scrollWheelZoom={true}
        className="h-full w-full"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution=""
        />
        <FitBounds locations={validLocs} />
        {validLocs.map((loc, i) => (
          <Marker
            key={`${loc.ip}-${i}`}
            position={[loc.latitude!, loc.longitude!]}
            icon={defaultIcon}
          >
            <Popup>
              <div className="text-xs font-mono text-gray-900">
                <strong>{loc.ip}</strong>
                <br />
                {loc.city && `${loc.city}, `}
                {loc.country}
                {loc.org && <><br />{loc.org}</>}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
