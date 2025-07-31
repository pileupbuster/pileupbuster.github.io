import { useEffect, useState, useRef } from 'react';
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
  systemStatus?: boolean | null;
}

interface PreviousUserData {
  user: CurrentActiveUser;
  qrzData?: QrzData;
  metadata?: QsoMetadata;
}

function CurrentActiveCallsign({ activeUser, qrzData, metadata, systemStatus }: CurrentActiveCallsignProps) {
  const [animationClass, setAnimationClass] = useState('');
  const [previousCallsign, setPreviousCallsign] = useState<string | null>(null);
  const [isAnimatingOut, setIsAnimatingOut] = useState(false);
  const [previousUserData, setPreviousUserData] = useState<PreviousUserData | null>(null);
  const animationTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    // Handle when activeUser changes
    if (activeUser && activeUser.callsign !== previousCallsign) {
      // Store the previous user data before updating
      if (previousCallsign && previousUserData) {
        // Keep showing previous user during animation
      }
      
      // Check if this is a direct QSO (not from queue)
      if (metadata?.source === 'direct') {
        console.log('Setting dissolve-in animation for direct QSO:', activeUser.callsign);
        setAnimationClass('dissolve-in-animation');
      } else {
        setAnimationClass('');
      }
      setPreviousCallsign(activeUser.callsign);
      setPreviousUserData({ user: activeUser, qrzData, metadata });
      setIsAnimatingOut(false);
      
      // Remove animation class after animation completes
      const timer = setTimeout(() => {
        setAnimationClass('');
      }, 800);
      
      return () => clearTimeout(timer);
    } else if (!activeUser && previousUserData && !isAnimatingOut) {
      // Handle when QSO ends (activeUser becomes null)
      console.log('QSO ended, starting animation out');
      setIsAnimatingOut(true);
      setAnimationClass('animating-out');
      
      // Clear any existing timer
      if (animationTimerRef.current) {
        clearTimeout(animationTimerRef.current);
      }
      
      // Clean up after animation
      animationTimerRef.current = setTimeout(() => {
        console.log('Animation out complete, clearing previous user data');
        setPreviousCallsign(null);
        setPreviousUserData(null);
        setIsAnimatingOut(false);
        setAnimationClass('');
        animationTimerRef.current = null;
      }, 1000);
    }
  }, [activeUser, metadata?.source, previousCallsign, isAnimatingOut, qrzData]);
  
  // Clean up timer on unmount
  useEffect(() => {
    return () => {
      if (animationTimerRef.current) {
        clearTimeout(animationTimerRef.current);
      }
    };
  }, []);

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
    const userToOpen = isAnimatingOut && previousUserData ? previousUserData.user : activeUser;
    if (userToOpen) {
      window.open(getQrzUrl(userToOpen.callsign), '_blank');
    }
  };

  // Determine which user to display (current or animating out previous)
  const displayUser = isAnimatingOut && previousUserData ? previousUserData.user : activeUser;
  const displayQrzData = isAnimatingOut && previousUserData ? previousUserData.qrzData : qrzData;
  const displayMetadata = isAnimatingOut && previousUserData ? previousUserData.metadata : metadata;
  
  console.log('CurrentActiveCallsign state:', {
    activeUser: activeUser?.callsign,
    isAnimatingOut,
    previousUserData: previousUserData?.user?.callsign,
    displayUser: displayUser?.callsign,
    animationClass
  });
  
  // If no user to display, show placeholder based on system status
  if (!displayUser) {
    console.log('Showing placeholder - no active user, systemStatus:', systemStatus);
    
    // When system is offline
    if (systemStatus === false) {
      return (
        <section className="current-active-section">
          <div className="current-active-card centered-layout">
            <div className="operator-image-large">
              <div className="placeholder-image offline-icon">🎙️</div>
            </div>
            <div className="active-info">
              <div className="active-callsign offline-text">Offline</div>
              <div className="active-name">Map shows last 24 hours activity</div>
              <div className="active-location">-</div>
            </div>
          </div>
        </section>
      );
    }
    
    // When system is online but no active callsign
    return (
      <section className="current-active-section">
        <div className="current-active-card centered-layout">
          <div className="operator-image-large">
            <div className="placeholder-image">👤</div>
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
  const hasQrzImage = displayQrzData?.image;
  const sourceDisplay = getQSOSourceDisplay(displayMetadata);
  const qsoDetails = getQSODetails(displayMetadata);
  
  console.log('Rendering active user:', displayUser?.callsign, 'with animation:', animationClass);
  
  return (
    <section className="current-active-section">
      <div className={`current-active-card centered-layout ${animationClass}`}>
        <div 
          className="operator-image-large clickable"
          onClick={handleAvatarClick}
          title={displayUser ? `View ${displayUser.callsign} on QRZ.com` : undefined}
          style={{ cursor: displayUser ? 'pointer' : 'default' }}
        >
          {hasQrzImage ? (
            <img src={displayQrzData.image} alt="Operator" className="operator-image" />
          ) : (
            <div className="placeholder-image">👤</div>
          )}
        </div>
        <div className="active-info">
          <a 
            href={getQrzUrl(displayUser.callsign)}
            target="_blank"
            rel="noopener noreferrer"
            className="active-callsign active-callsign-link"
          >
            {displayUser.callsign}
          </a>
          <div className="active-name">{displayUser.name}</div>
          <div className="active-location">{displayUser.location}</div>
          
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
          
          {displayQrzData?.url && (
            <button 
              className="qrz-button"
              onClick={() => window.open(displayQrzData.url, '_blank')}
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
