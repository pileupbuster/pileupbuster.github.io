import QueueItem from './QueueItem'
import type { QueueItemData } from './QueueItem'

export interface WaitingQueueProps {
  queueData: QueueItemData[]
}

export default function WaitingQueue({ queueData }: WaitingQueueProps) {
  return (
    <section className="queue-section">
      <h2 className="queue-title">Waiting Queue</h2>
      <div className="queue-container">
        {queueData.map((item, index) => (
          <QueueItem key={index} item={item} index={index} />
        ))}
      </div>
    </section>
  )
}
