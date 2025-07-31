/**
 * Formats country display with state in parentheses for US addresses
 */
export function formatCountryWithState(dxccName?: string, address?: string): string {
  // If no country name, return 'Unknown'
  if (!dxccName) {
    return 'Unknown';
  }

  // Check if it's United States
  if (dxccName === 'United States') {
    // Try to extract state from address
    if (address) {
      // Split address by comma and trim each part
      const parts = address.split(',').map(part => part.trim());
      
      // US addresses often have format: "City, State ZIP" or "City, State"
      if (parts.length >= 2) {
        // Look for state code pattern (2 uppercase letters)
        for (let i = parts.length - 1; i >= 0; i--) {
          const part = parts[i];
          
          // Check for state code in "XX 12345" format
          const stateZipMatch = part.match(/^([A-Z]{2})\s+\d{5}$/);
          if (stateZipMatch) {
            return `${dxccName} (${stateZipMatch[1]})`;
          }
          
          // Check for standalone state code
          const stateMatch = part.match(/^([A-Z]{2})$/);
          if (stateMatch) {
            return `${dxccName} (${stateMatch[1]})`;
          }
        }
      }
    }
  }

  // For non-US or if we couldn't find state, just return the country
  return dxccName;
}