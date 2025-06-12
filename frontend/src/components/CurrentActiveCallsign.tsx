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
          <img src="https://cdn-bio.qrz.com/b/ei5jdb/to_use_21st_May.jpg" alt="Operator" className="operator-image" />
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
