import React from 'react';
import Timer from './Timer';

export interface QueueItemData {
  callsign: string
  location: string
  timestamp: string
  qrz?: {
    callsign?: string
    name?: string
    address?: string
    dxcc_name?: string
    image?: string
    error?: string
  }
}

export interface QueueItemProps {
  item: QueueItemData
  index: number
  isAdminLoggedIn?: boolean
}

export default function QueueItem({ item, index, isAdminLoggedIn }: QueueItemProps) {
  const [imageLoadFailed, setImageLoadFailed] = React.useState(false);
  const hasQrzImage = item.qrz?.image && !item.qrz?.error && !imageLoadFailed;
  
  // Reset image load failure state when image URL changes
  React.useEffect(() => {
    setImageLoadFailed(false);
  }, [item.qrz?.image]);
  
  return (
    <div key={index} className="callsign-card">
      <div className="operator-image">
        {hasQrzImage ? (
          <img 
            src={item.qrz.image} 
            alt={`${item.callsign} profile`}
            className="operator-image-qrz"
            onError={() => {
              setImageLoadFailed(true);
            }}
          />
        ) : (
          <div className="placeholder-image">👤</div>
        )}
      </div>
      <div className="card-info">
        <div className="card-callsign">{item.callsign}</div>
        <div className="card-location">{item.location}</div>
        {/* Timer is only shown to admin users */}
        {isAdminLoggedIn && <Timer timestamp={item.timestamp} />}
      </div>
    </div>
  )
}
