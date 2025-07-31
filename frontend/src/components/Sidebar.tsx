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
  const openProfile = (callsign: string) => {
    window.open(`https://www.qrz.com/db/${callsign}`, '_blank');
  };
  return (
    <aside className="sidebar">
      {/* Current Operator Section */}
      <div className="current-operator-section">
        <div 
          className="current-operator-card" 
          onClick={() => currentOperator && openProfile(currentOperator.callsign)}
          style={{ cursor: currentOperator ? 'pointer' : 'default' }}
        >
          {currentOperator ? (
            currentOperator.profileImage ? (
              <img 
                src={currentOperator.profileImage} 
                alt={currentOperator.callsign} 
                className="current-operator-image" 
              />
            ) : (
              <div className="current-operator-image placeholder-image">👤</div>
            )
          ) : (
            <div className="current-operator-image placeholder-radio">
              📻
            </div>
          )}
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
