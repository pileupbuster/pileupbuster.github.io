import { QRZ_LOOKUP_URL_TEMPLATE } from '../config/api';

export interface CurrentActiveUser {
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

interface QsoMetadata {
  source?: 'queue' | 'direct' | 'queue_specific';
  bridge_initiated?: boolean;
  frequency_mhz?: number;
  mode?: string;
  started_via?: string;
}

interface CurrentActiveCallsignProps {
  activeUser: CurrentActiveUser | null;
  qrzData?: QrzData;
  metadata?: QsoMetadata;
  onCompleteQso?: () => Promise<void>;
  isAdminLoggedIn?: boolean;
}

function CurrentActiveCallsign({ activeUser, qrzData, metadata, onCompleteQso, isAdminLoggedIn }: CurrentActiveCallsignProps) {
  // Helper function to generate QRZ lookup URL for a callsign
  const getQrzUrl = (callsign: string): string => {
    return QRZ_LOOKUP_URL_TEMPLATE.replace('{CALLSIGN}', callsign);
  };

  // Get QSO source display information
  const getQSOSourceDisplay = (metadata?: QsoMetadata) => {
    if (!metadata) return null;
    
    if (metadata.bridge_initiated) {
      return metadata.source === 'queue' 
        ? { text: '👥 Worked from Pileup Buster (via QLog)', className: 'qso-source bridge-queue' }
        : { text: '📻 Worked Direct (via QLog)', className: 'qso-source bridge-direct' };
    }
    
    // Handle logging software initiated QSOs
    if (metadata.started_via === 'logging_software') {
      return metadata.source === 'queue' 
        ? { text: '👥 Worked from Pileup Buster', className: 'qso-source manual-queue' }
        : { text: '📻 Worked Direct', className: 'qso-source manual-direct' };
    }
    
    // Default case - check source type
    if (metadata.source === 'queue' || metadata.source === 'queue_specific') {
      return { text: '👥 Worked from Pileup Buster', className: 'qso-source manual-queue' };
    }
    
    return { text: '📻 Worked Direct', className: 'qso-source manual-direct' };
  };

  // Get QSO details (frequency/mode) for bridge or logging software QSOs
  const getQSODetails = (metadata?: QsoMetadata) => {
    if (!metadata) return null;
    
    // Show details for bridge QSOs OR logging software QSOs
    if (metadata.bridge_initiated || metadata.started_via === 'logging_software') {
      const details = [];
      if (metadata.frequency_mhz) {
        details.push(`📡 ${metadata.frequency_mhz} MHz`);
      }
      if (metadata.mode) {
        details.push(`📻 ${metadata.mode}`);
      }
      
      return details.length > 0 ? details.join(' • ') : null;
    }
    
    return null;
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
  const sourceDisplay = getQSOSourceDisplay(metadata);
  const qsoDetails = getQSODetails(metadata);
  
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
          
          {/* QSO Source Indicator */}
          {sourceDisplay && (
            <div className={sourceDisplay.className}>
              {sourceDisplay.text}
            </div>
          )}
          
          {/* QSO Details (frequency/mode) for bridge or logging software QSOs */}
          {qsoDetails && (
            <div className="bridge-qso-details">
              {qsoDetails}
            </div>
          )}
          
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
