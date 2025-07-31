import CurrentActiveCallsign from './CurrentActiveCallsign';
import type { CurrentActiveUser } from './CurrentActiveCallsign';

interface CurrentOperator {
  callsign: string;
  name: string;
  location: string;
  coordinates: { lat: number; lon: number };
  profileImage: string;
  qrz?: {
    name?: string;
    address?: string;
    image?: string;
    url?: string;
  };
  metadata?: {
    source?: 'queue' | 'direct' | 'queue_specific';
    bridge_initiated?: boolean;
    frequency_mhz?: number;
    mode?: string;
    started_via?: string;
  };
}

interface SidebarProps {
  currentOperator: CurrentOperator | null;
  queueCount: number;
  workedCount: number;
  onWorkOperator: () => void;
  onCompleteQso?: () => Promise<void>;
  isAdminLoggedIn?: boolean;
}

function Sidebar({ currentOperator, queueCount, workedCount, onWorkOperator: _onWorkOperator, onCompleteQso, isAdminLoggedIn }: SidebarProps) {
  // Convert CurrentOperator to CurrentActiveUser format
  const activeUser: CurrentActiveUser | null = currentOperator ? {
    callsign: currentOperator.callsign,
    name: currentOperator.name,
    location: currentOperator.location
  } : null;

  return (
    <aside className="sidebar">
      {/* Current Operator Section */}
      <CurrentActiveCallsign 
        activeUser={activeUser}
        qrzData={currentOperator?.qrz}
        metadata={currentOperator?.metadata}
        onCompleteQso={onCompleteQso}
        isAdminLoggedIn={isAdminLoggedIn}
      />

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
