import { useState } from 'react'

export interface AddQueueItemProps {
  onAddCallsign: (callsign: string) => void
}

export default function AddQueueItem({ onAddCallsign }: AddQueueItemProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [callsign, setCallsign] = useState('')

  const handleClick = () => {
    setIsEditing(true)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      if (callsign.trim()) {
        onAddCallsign(callsign.trim().toUpperCase())
        setCallsign('')
      }
      setIsEditing(false)
    } else if (e.key === 'Escape') {
      setCallsign('')
      setIsEditing(false)
    }
  }

  const handleBlur = () => {
    setCallsign('')
    setIsEditing(false)
  }

  return (
    <div className="callsign-card add-queue-item" onClick={handleClick}>
      {isEditing ? (
        <input
          type="text"
          value={callsign}
          onChange={(e) => setCallsign(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          placeholder="CALLSIGN"
          className="callsign-input"
          autoFocus
          maxLength={10}
        />
      ) : (
        <div className="add-icon">➕</div>
      )}
    </div>
  )
}
