import { useState } from 'react'

export interface AddQueueItemProps {
  onAddCallsign: (callsign: string) => Promise<void>
}

export default function AddQueueItem({ onAddCallsign }: AddQueueItemProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [callsign, setCallsign] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleClick = () => {
    if (!isSubmitting) {
      setIsEditing(true)
    }
  }

  const handleSubmit = async () => {
    if (callsign.trim() && !isSubmitting) {
      setIsSubmitting(true)
      try {
        await onAddCallsign(callsign.trim().toUpperCase())
        setCallsign('')
        setIsEditing(false)
      } catch (error) {
        // Error is handled in parent component
        console.error('Error submitting callsign:', error)
      } finally {
        setIsSubmitting(false)
      }
    }
  }

  const handleKeyDown = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      await handleSubmit()
    } else if (e.key === 'Escape') {
      setCallsign('')
      setIsEditing(false)
    }
  }

  const handleBlur = () => {
    if (!isSubmitting) {
      setCallsign('')
      setIsEditing(false)
    }
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
          placeholder={isSubmitting ? "SUBMITTING..." : "CALLSIGN"}
          className="callsign-input"
          autoFocus
          maxLength={10}
          disabled={isSubmitting}
        />
      ) : (
        <div className="add-icon">➕</div>
      )}
    </div>
  )
}
