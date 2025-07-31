interface HeaderFrequencyDisplayProps {
  frequency: string;
  systemStatus?: boolean | null;
  split?: string;
}

function HeaderFrequencyDisplay({ frequency, systemStatus, split }: HeaderFrequencyDisplayProps) {
  // Rule: We are offline = NOT VISIBLE!
  if (systemStatus === false) {
    return null; // Component is completely hidden when offline
  }

  // When online but no frequency, show "ON AIR"
  if (!frequency || frequency.trim() === '') {
    return (
      <div className="frequency-section">
        <div className="frequency-value">ON AIR</div>
        {split && (
          <div className="split-display">SPLIT {split}</div>
        )}
      </div>
    );
  }

  // When online with frequency, show "ON AIR frequency MHz" on one line, split below
  return (
    <div className="frequency-section">
      <div className="frequency-value">ON AIR {frequency} MHz</div>
      {split && (
        <div className="split-display">SPLIT {split}</div>
      )}
    </div>
  );
}

export default HeaderFrequencyDisplay;
