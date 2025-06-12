import { useState } from 'react'
import './App.css'

// Sample data for demonstration
const sampleQueueData = [
  { callsign: 'WP3XZ', location: 'San Juan, Puerto Rico' },
  { callsign: 'K4ABC', location: 'Atlanta, Georgia' },
  { callsign: 'VE7XYZ', location: 'Vancouver, Canada' },
  { callsign: 'JA1DEF', location: 'Tokyo, Japan' },
  { callsign: 'G0GHI', location: 'London, England' },
]

const currentActiveUser = {
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
        <section className="current-active-section">
          <div className="current-active-card">
            <div className="operator-image-large">
              <div className="placeholder-image">👤</div>
            </div>
            <div className="active-info">
              <div className="active-callsign">{currentActiveUser.callsign}</div>
              <div className="active-name">{currentActiveUser.name}</div>
              <div className="active-location">{currentActiveUser.location}</div>
              <button className="qrz-button">QRZ.COM INFO</button>
            </div>
          </div>
        </section>

        {/* Waiting Queue Container (Red Border) */}
        <section className="queue-section">
          <h2 className="queue-title">Waiting Queue</h2>
          <div className="queue-container">
            {sampleQueueData.map((item, index) => (
              <div key={index} className="callsign-card">
                <div className="operator-image">
                  <div className="placeholder-image">👤</div>
                </div>
                <div className="card-info">
                  <div className="card-callsign">{item.callsign}</div>
                  <div className="card-location">{item.location}</div>
                </div>
              </div>
            ))}
          </div>
        </section>
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
