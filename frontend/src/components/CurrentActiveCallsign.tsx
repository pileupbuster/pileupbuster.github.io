import { QRZ_LOOKUP_URL_TEMPLATE } from '../config/api';

interface CurrentActiveUser {
  callsign: string;
  name: string;
  location: string;
}

interface QrzData {
  name?: string;
  address?: string;
  image?: string;
  url?: string;
}

interface CurrentActiveCallsignProps {
  activeUser: CurrentActiveUser | null;
  qrzData?: QrzData;
  onCompleteQso?: () => Promise<void>;
  isAdminLoggedIn?: boolean;
}

function CurrentActiveCallsign({ activeUser, qrzData, onCompleteQso, isAdminLoggedIn }: CurrentActiveCallsignProps) {
  // Helper function to generate QRZ lookup URL for a callsign
  const getQrzUrl = (callsign: string): string => {
    return QRZ_LOOKUP_URL_TEMPLATE.replace('{CALLSIGN}', callsign);
  };

  // Handle avatar/image click for admin complete QSO action
  const handleAvatarClick = async (e: React.MouseEvent) => {
    e.preventDefault();
    if (isAdminLoggedIn && onCompleteQso && activeUser) {
      try {
        await onCompleteQso();
      } catch (error) {
        console.error('Failed to complete QSO:', error);
      }
    }
  };

  // If no active user, show placeholder
  if (!activeUser) {
    return (
      <section className="current-active-section">
        <div className="current-active-card">
          <div className="operator-image-large">
            <div className="placeholder-image" style={{ fontSize: '3rem' }}>👤</div>
          </div>
          <div className="active-info">
            <div className="active-callsign">No active callsign</div>
            <div className="active-name">Waiting for next QSO</div>
            <div className="active-location">-</div>
          </div>
        </div>
      </section>
    );
  }

  // Determine which image to show
  const hasQrzImage = qrzData?.image;
  
  return (
    <section className="current-active-section">
      <div className="current-active-card">
        <div 
          className={`operator-image-large ${isAdminLoggedIn && activeUser ? 'admin-clickable' : ''}`}
          onClick={handleAvatarClick}
          title={isAdminLoggedIn && activeUser ? 'Click to complete current QSO' : undefined}
        >
          {hasQrzImage ? (
            <img src={qrzData.image} alt="Operator" className="operator-image" />
          ) : (
            <div className="placeholder-image" style={{ fontSize: '3rem' }}>👤</div>
          )}
        </div>
        <div className="active-info">
          <a 
            href={getQrzUrl(activeUser.callsign)}
            target="_blank"
            rel="noopener noreferrer"
            className="active-callsign active-callsign-link"
          >
            {activeUser.callsign}
          </a>
          <div className="active-name">{activeUser.name}</div>
          <div className="active-location">{activeUser.location}</div>
          {qrzData?.url && (
            <button 
              className="qrz-button"
              onClick={() => window.open(qrzData.url, '_blank')}
            >
              QRZ.COM INFO
            </button>
          )}
        </div>
      </div>
    </section>
  );
}

export default CurrentActiveCallsign;
export type { CurrentActiveUser };
