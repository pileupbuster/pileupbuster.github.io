import { useState } from 'react'
import './App.css'
import CurrentActiveCallsign, { type CurrentActiveUser } from './components/CurrentActiveCallsign'
import WaitingQueue, { type QueueItem } from './components/WaitingQueue'

// Sample data for demonstration
const sampleQueueData: QueueItem[] = [
  { callsign: 'WP3XZ', location: 'San Juan, Puerto Rico' },
  { callsign: 'K4ABC', location: 'Atlanta, Georgia' },
  { callsign: 'VE7XYZ', location: 'Vancouver, Canada' },
  { callsign: 'JA1DEF', location: 'Tokyo, Japan' },
  { callsign: 'G0GHI', location: 'London, England' },
]

const currentActiveUser: CurrentActiveUser = {
  callsign: 'WP3XYZ',
  name: 'John Smith',
  location: 'San Juan, Puerto Rico'
}

function App() {
  const [callsignInput, setCallsignInput] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    // TODO: Backend integration will be added later
    console.log('Processing callsign:', callsignInput)
    setCallsignInput('')
  }

  return (
    <div className="pileup-buster-app">
      {/* Header */}
      <header className="header">
        <div className="hamburger-menu">
          <div className="hamburger-line"></div>
          <div className="hamburger-line"></div>
          <div className="hamburger-line"></div>
        </div>
        <h1 className="title">PILEUP BUSTER</h1>
      </header>

      <main className="main-content">
        {/* Current Active Callsign (Green Border) */}
        <CurrentActiveCallsign activeUser={currentActiveUser} />

        {/* Waiting Queue Container (Red Border) */}
        <WaitingQueue queueData={sampleQueueData} />
      </main>

      {/* Callsign Entry Form (Blue Border) */}
      <footer className="entry-form-section">
        <form onSubmit={handleSubmit} className="entry-form">
          <input
            type="text"
            value={callsignInput}
            onChange={(e) => setCallsignInput(e.target.value.toUpperCase())}
            placeholder="Enter call sign"
            className="callsign-input"
          />
          <button type="submit" className="process-button">
            PROCESS
          </button>
        </form>
      </footer>
    </div>
  )
}

export default App
