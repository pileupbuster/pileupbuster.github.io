import QueueItem from './QueueItem'
import AddQueueItem from './AddQueueItem'
import type { QueueItemData } from './QueueItem'

export interface WaitingQueueProps {
  queueData: QueueItemData[]
  onAddCallsign: (callsign: string) => Promise<void>
}

export default function WaitingQueue({ queueData, onAddCallsign }: WaitingQueueProps) {
  const handleAddCallsign = async (callsign: string) => {
    try {
      await onAddCallsign(callsign)
    } catch (error) {
      // Error handling could be improved with user notifications
      console.error('Failed to add callsign:', error)
      alert(`Failed to add callsign: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  const showAddButton = queueData.length < 4

  return (
    <section className="queue-section">
      <h2 className="queue-title">Waiting Queue</h2>
      <div className="queue-container">
        {queueData.map((item, index) => (
          <QueueItem key={`${item.callsign}-${index}`} item={item} index={index} />
        ))}
        {showAddButton && (
          <AddQueueItem onAddCallsign={handleAddCallsign} />
        )}
      </div>
    </section>
  )
}
