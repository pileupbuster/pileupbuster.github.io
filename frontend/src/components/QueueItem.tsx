export interface QueueItemData {
  callsign: string
  location: string
}

export interface QueueItemProps {
  item: QueueItemData
  index: number
}

export default function QueueItem({ item, index }: QueueItemProps) {
  return (
    <div key={index} className="callsign-card">
      <div className="operator-image">
        <div className="placeholder-image">👤</div>
      </div>
      <div className="card-info">
        <div className="card-callsign">{item.callsign}</div>
        <div className="card-location">{item.location}</div>
      </div>
    </div>
  )
}
