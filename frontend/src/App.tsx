import './App.css'
import CurrentActiveCallsign, { type CurrentActiveUser } from './components/CurrentActiveCallsign'
import WaitingQueue from './components/WaitingQueue'
import { type QueueItemData } from './components/QueueItem'

// Sample data for demonstration
const sampleQueueData: QueueItemData[] = [
  { callsign: 'EI6JGB', location: 'San Juan, Puerto Rico' },
  { callsign: 'EI5JBB', location: 'Atlanta, Georgia' },
  { callsign: 'EI2HF', location: 'Vancouver, Canada' },
  
]

const currentActiveUser: CurrentActiveUser = {
  callsign: 'EI5JDB',
  name: 'Jack Daniels Burbon',
  location: 'Near Jamie, Clonmel, Ireland',
}

function App() {

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
    </div>
  )
}

export default App
