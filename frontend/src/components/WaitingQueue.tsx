import QueueItem from './QueueItem'
import AddQueueItem from './AddQueueItem'
import type { QueueItemData } from './QueueItem'

export interface WaitingQueueProps {
  queueData: QueueItemData[]
  queueTotal: number
  queueMaxSize: number
  onAddCallsign: (callsign: string) => Promise<void>
  onWorkNext?: (callsign: string) => Promise<void>
  isAdminLoggedIn?: boolean
  systemActive?: boolean
}

export default function WaitingQueue({ 
  queueData, 
  queueTotal, 
  queueMaxSize, 
  onAddCallsign, 
  onWorkNext,
  isAdminLoggedIn,
  systemActive = true 
}: WaitingQueueProps) {
  const handleAddCallsign = async (callsign: string) => {
    try {
      await onAddCallsign(callsign)
    } catch (error) {
      // Error handling could be improved with user notifications
      console.error('Failed to add callsign:', error)
      alert(`Failed to add callsign: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  const isQueueFull = queueTotal >= queueMaxSize
  const showAddButton = !isQueueFull && systemActive

  return (
    <section className="queue-section">
      <h2 className="queue-title">
        Waiting Queue ({queueTotal}/{queueMaxSize})
      </h2>
      
      {/* Queue status messaging */}
      {isQueueFull && systemActive && (
        <div className="alert-warning">
          ⚠️ Queue is currently full ({queueTotal}/{queueMaxSize}). Please wait for a spot to open up and try again.
        </div>
      )}
      
      <div className="queue-container">
        {queueData.map((item, index) => (
          <QueueItem 
            key={`${item.callsign}-${index}`} 
            item={item} 
            index={index} 
            onWorkNext={onWorkNext}
            isAdminLoggedIn={isAdminLoggedIn}
          />
        ))}
        {showAddButton && (
          <AddQueueItem onAddCallsign={handleAddCallsign} />
        )}
      </div>
    </section>
  )
}
