import QueueItem from './QueueItem'
import AddQueueItem from './AddQueueItem'
import type { QueueItemData } from './QueueItem'

export interface WaitingQueueProps {
  queueData: QueueItemData[]
}

export default function WaitingQueue({ queueData }: WaitingQueueProps) {
  const handleAddCallsign = (callsign: string) => {
    // TODO: Implement backend call to add callsign
    console.log('Adding callsign:', callsign)
  }

  const showAddButton = queueData.length < 4

  return (
    <section className="queue-section">
      <h2 className="queue-title">Waiting Queue</h2>
      <div className="queue-container">
        {queueData.map((item, index) => (
          <QueueItem key={index} item={item} index={index} />
        ))}
        {showAddButton && (
          <AddQueueItem onAddCallsign={handleAddCallsign} />
        )}
      </div>
    </section>
  )
}
