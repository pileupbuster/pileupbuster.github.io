import { useState } from 'react'

export interface ScaleControlProps {
  onScaleChange: (scale: number) => void;
  defaultScale?: number;
}

const ScaleControl: React.FC<ScaleControlProps> = ({ onScaleChange, defaultScale = 1 }) => {
  const [scale, setScale] = useState(defaultScale);

  const handleScaleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newScale = parseFloat(event.target.value);
    setScale(newScale);
    onScaleChange(newScale);
  };

  return (
    <div className="scale-control">
      <label htmlFor="scale-slider" className="scale-label">UI Scale:</label>
      <input
        id="scale-slider"
        type="range"
        min="0.5"
        max="1.5"
        step="0.1"
        value={scale}
        onChange={handleScaleChange}
        className="scale-slider"
      />
      <span className="scale-value">{Math.round(scale * 100)}%</span>
    </div>
  );
};

export default ScaleControl;
