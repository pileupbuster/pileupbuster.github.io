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
}

function CurrentActiveCallsign({ activeUser, qrzData, metadata }: CurrentActiveCallsignProps) {
  // Helper function to generate QRZ lookup URL for a callsign
  const getQrzUrl = (callsign: string): string => {
    return QRZ_LOOKUP_URL_TEMPLATE.replace('{CALLSIGN}', callsign);
  };

  // Get QSO source display information
  const getQSOSourceDisplay = (metadata?: QsoMetadata) => {
    if (!metadata) return { text: '👥 Worked from Pileup Buster', className: 'qso-source manual-queue' };
    
    // If metadata exists but source is not specified, assume it's from queue
    if (!metadata.source) {
      return { text: '👥 Worked from Pileup Buster', className: 'qso-source manual-queue' };
    }
    
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
    
    // Check source type
    if (metadata.source === 'queue' || metadata.source === 'queue_specific') {
      return { text: '👥 Worked from Pileup Buster', className: 'qso-source manual-queue' };
    }
    
    // Only show "Worked Direct" if explicitly marked as direct
    if (metadata.source === 'direct') {
      return { text: '📻 Worked Direct', className: 'qso-source manual-direct' };
    }
    
    // Default to queue if source is unknown
    return { text: '👥 Worked from Pileup Buster', className: 'qso-source manual-queue' };
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

  // Handle avatar/image click to open QRZ profile
  const handleAvatarClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (activeUser) {
      window.open(getQrzUrl(activeUser.callsign), '_blank');
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
          className="operator-image-large clickable"
          onClick={handleAvatarClick}
          title={activeUser ? `View ${activeUser.callsign} on QRZ.com` : undefined}
          style={{ cursor: activeUser ? 'pointer' : 'default' }}
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
