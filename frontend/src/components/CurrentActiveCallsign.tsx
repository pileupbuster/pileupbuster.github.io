interface CurrentActiveUser {
  callsign: string;
  name: string;
  location: string;
}

interface CurrentActiveCallsignProps {
  activeUser: CurrentActiveUser;
}

function CurrentActiveCallsign({ activeUser }: CurrentActiveCallsignProps) {
  return (
    <section className="current-active-section">
      <div className="current-active-card">
        <div className="operator-image-large">
          <div className="placeholder-image">👤</div>
        </div>
        <div className="active-info">
          <div className="active-callsign">{activeUser.callsign}</div>
          <div className="active-name">{activeUser.name}</div>
          <div className="active-location">{activeUser.location}</div>
          <button className="qrz-button">QRZ.COM INFO</button>
        </div>
      </div>
    </section>
  );
}

export default CurrentActiveCallsign;
export type { CurrentActiveUser };
