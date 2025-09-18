import React from 'react'
import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

// Fix for default markers in React Leaflet
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

const Map = ({ 
  data = [], 
  center = [39.8283, -98.5795], // Center of USA
  zoom = 4,
  className = '',
  showHeatmap = false,
  onLocationClick = null
}) => {
  // Custom icon for universities/locations
  const universityIcon = new L.Icon({
    iconUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMTMuMDkgOC4yNkwyMCA5TDEzLjA5IDE1Ljc0TDEyIDIyTDEwLjkxIDE1Ljc0TDQgOUwxMC45MSA4LjI2TDEyIDJaIiBmaWxsPSIjMzMzIiBzdHJva2U9IiNmZmYiIHN0cm9rZS13aWR0aD0iMiIvPgo8L3N2Zz4K',
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32],
  })

  // Process data for mapping
  const mapData = data.map(item => ({
    id: item.id || Math.random(),
    position: item.coordinates || [item.lat, item.lng],
    title: item.title || item.name,
    description: item.description || '',
    value: item.value || 0,
    athletes: item.athletes || 0,
    ...item
  }))

  const renderMarkers = () => {
    return mapData.map((item) => {
      if (showHeatmap && item.value) {
        // Render heat map circles
        const radius = Math.max(5, Math.min(50, item.value / 2))
        const fillOpacity = Math.max(0.3, Math.min(0.8, item.value / 100))
        
        return (
          <CircleMarker
            key={item.id}
            center={item.position}
            radius={radius}
            fillColor="#3b82f6"
            color="#1d4ed8"
            weight={2}
            fillOpacity={fillOpacity}
            eventHandlers={{
              click: () => onLocationClick && onLocationClick(item)
            }}
          >
            <Popup>
              <div className="text-center">
                <h3 className="font-semibold">{item.title}</h3>
                {item.description && (
                  <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                )}
                <div className="mt-2 text-sm">
                  <div><strong>Value:</strong> {item.value}</div>
                  {item.athletes && <div><strong>Athletes:</strong> {item.athletes}</div>}
                </div>
              </div>
            </Popup>
          </CircleMarker>
        )
      } else {
        // Render standard markers
        return (
          <Marker
            key={item.id}
            position={item.position}
            icon={universityIcon}
            eventHandlers={{
              click: () => onLocationClick && onLocationClick(item)
            }}
          >
            <Popup>
              <div className="text-center">
                <h3 className="font-semibold">{item.title}</h3>
                {item.description && (
                  <p className="text-sm text-gray-600 mt-1">{item.description}</p>
                )}
                {item.athletes && (
                  <div className="mt-2 text-sm">
                    <strong>Active Athletes:</strong> {item.athletes}
                  </div>
                )}
              </div>
            </Popup>
          </Marker>
        )
      }
    })
  }

  return (
    <div className={`rounded-lg overflow-hidden ${className}`}>
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        className="z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {renderMarkers()}
      </MapContainer>
    </div>
  )
}

export default Map