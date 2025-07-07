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
  onWorkNext?: (callsign: string) => Promise<void>
  isAdminLoggedIn?: boolean
}

export default function QueueItem({ item, index, onWorkNext, isAdminLoggedIn }: QueueItemProps) {
  const [imageLoadFailed, setImageLoadFailed] = React.useState(false);
  const hasQrzImage = item.qrz?.image && !item.qrz?.error && !imageLoadFailed;
  
  // Reset image load failure state when image URL changes
  React.useEffect(() => {
    setImageLoadFailed(false);
  }, [item.qrz?.image]);

  // Handle avatar/image click for admin work next action
  const handleAvatarClick = async (e: React.MouseEvent) => {
    e.preventDefault();
    if (isAdminLoggedIn && onWorkNext) {
      try {
        await onWorkNext(item.callsign);
      } catch (error) {
        console.error('Failed to work next user:', error);
      }
    }
  };
  
  return (
    <div key={index} className="callsign-card">
      <div 
        className={`operator-image ${isAdminLoggedIn ? 'admin-clickable' : ''}`}
        onClick={handleAvatarClick}
        title={isAdminLoggedIn ? `Click to work ${item.callsign} next` : undefined}
      >
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
        <Timer timestamp={item.timestamp} />
      </div>
    </div>
  )
}
