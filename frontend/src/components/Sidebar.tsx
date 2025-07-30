interface CurrentOperator {
  callsign: string;
  name: string;
  location: string;
  coordinates: { lat: number; lon: number };
  profileImage: string;
}

interface SidebarProps {
  currentOperator: CurrentOperator | null;
  queueCount: number;
  workedCount: number;
  onWorkOperator: () => void;
}

function Sidebar({ currentOperator, queueCount, workedCount, onWorkOperator }: SidebarProps) {
  return (
    <aside className="sidebar">
      {/* Current Operator Section */}
      <div className="current-operator-section">
        <div className="current-operator-card" onClick={onWorkOperator}>
          <img 
            src={currentOperator?.profileImage || 'https://i.pravatar.cc/200?img=68'} 
            alt={currentOperator?.callsign || 'Waiting'} 
            className="current-operator-image" 
          />
          <div className="current-operator-info">
            <h2 className="current-callsign">
              {currentOperator?.callsign || 'No Active QSO'}
            </h2>
            <p className="current-name">
              {currentOperator?.name || 'Waiting for Callers'}
            </p>
            <p className="current-location">
              {currentOperator?.location || 'Queue is empty'}
            </p>
          </div>
        </div>
      </div>

      {/* Queue Stats */}
      <div className="queue-stats">
        <div className="stat-item">
          <span className="stat-label">In Queue</span>
          <span className="stat-value">{queueCount}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Worked</span>
          <span className="stat-value">{workedCount}</span>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
