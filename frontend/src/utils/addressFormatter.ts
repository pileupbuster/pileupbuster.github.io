/**
 * Formats an address to show only country, or country + state for US addresses
 */
export function formatLocationDisplay(address?: string, dxccName?: string): string {
  // If no address, fall back to dxcc_name or 'Unknown'
  if (!address) {
    return dxccName || 'Unknown';
  }

  // Split address by comma and trim each part
  const parts = address.split(',').map(part => part.trim());
  
  // If address has less than 2 parts, return as is
  if (parts.length < 2) {
    return address;
  }

  // Get the last part (usually country)
  const country = parts[parts.length - 1];
  
  // Check if it's a US address (country is USA, US, United States, or contains a US state code)
  const isUSA = /^(USA?|United States|United States of America)$/i.test(country) ||
                /^[A-Z]{2}$/.test(country); // Two letter state code
  
  if (isUSA) {
    // For US addresses, try to find the state
    if (parts.length >= 3) {
      // Typical format: "City, State, Country" or "City, State ZIP, Country"
      const stateOrZip = parts[parts.length - 2];
      
      // Extract state code from "State ZIP" format
      const stateMatch = stateOrZip.match(/^([A-Z]{2})\s+\d{5}/);
      if (stateMatch) {
        return `USA, ${stateMatch[1]}`;
      }
      
      // Check if it's just a state code
      const justState = stateOrZip.match(/^([A-Z]{2})$/);
      if (justState) {
        return `USA, ${justState[1]}`;
      }
      
      // For full state names or other formats, return as is
      if (stateOrZip.length > 2 && !stateOrZip.match(/^\d/)) {
        return `USA, ${stateOrZip}`;
      }
    }
    
    // If we can't find state info, just return USA
    return 'USA';
  }
  
  // For non-US addresses, return just the country
  return country;
}