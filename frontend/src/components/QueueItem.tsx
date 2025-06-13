export interface QueueItemData {
  callsign: string
  location: string
  qrz?: {
    callsign?: string
    name?: string
    address?: string
    image?: string
    error?: string
  }
}

export interface QueueItemProps {
  item: QueueItemData
  index: number
}

export default function QueueItem({ item, index }: QueueItemProps) {
  const hasQrzImage = item.qrz?.image && !item.qrz?.error;
  
  return (
    <div key={index} className="callsign-card">
      <div className="operator-image">
        {hasQrzImage ? (
          <img 
            src={item.qrz.image} 
            alt={`${item.callsign} profile`}
            className="operator-image-qrz"
            onError={(e) => {
              // Fallback to placeholder if image fails to load
              const target = e.target as HTMLImageElement;
              target.style.display = 'none';
              target.nextElementSibling?.classList.remove('hidden');
            }}
          />
        ) : null}
        <div className={`placeholder-image ${hasQrzImage ? 'hidden' : ''}`}>👤</div>
      </div>
      <div className="card-info">
        <div className="card-callsign">{item.callsign}</div>
        <div className="card-location">{item.location}</div>
      </div>
    </div>
  )
}
