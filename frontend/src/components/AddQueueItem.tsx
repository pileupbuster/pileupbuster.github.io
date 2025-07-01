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

  const handleInputFocus = (e: React.FocusEvent<HTMLInputElement>) => {
    // Prevent mobile viewport jumping by ensuring the input stays in view
    setTimeout(() => {
      e.target.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'center',
        inline: 'nearest'
      })
    }, 100)
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
      e.preventDefault() // Prevent form submission behavior
      await handleSubmit()
    } else if (e.key === 'Escape') {
      setCallsign('')
      setIsEditing(false)
    } else if (e.key === 'Tab') {
      // Prevent tab navigation on mobile to avoid jumping to other inputs
      e.preventDefault()
    }
  }

  const handleBlur = () => {
    if (!isSubmitting) {
      // Small delay to allow click events to process before hiding
      setTimeout(() => {
        setCallsign('')
        setIsEditing(false)
      }, 150)
    }
  }

  return (
    <div className="callsign-card add-queue-item" onClick={handleClick}>
      {isEditing ? (
        <div className="callsign-input-container">
          <input
            type="text"
            value={callsign}
            onChange={(e) => setCallsign(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={handleBlur}
            onFocus={handleInputFocus}
            placeholder={isSubmitting ? "SUBMITTING..." : "CALLSIGN"}
            className="callsign-input"
            autoFocus
            maxLength={10}
            disabled={isSubmitting}
            enterKeyHint="done"
            inputMode="text"
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="characters"
            spellCheck="false"
          />
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!callsign.trim() || isSubmitting}
            className="callsign-submit-button"
          >
            ✓
          </button>
        </div>
      ) : (
        <div className="add-icon">➕</div>
      )}
    </div>
  )
}
