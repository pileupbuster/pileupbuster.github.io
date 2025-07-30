# Worked Callers Functionality

## Overview

The Pileup Buster system now includes a "worked callers" feature that tracks all stations you have worked (completed QSOs with) since the system was activated. This feature automatically manages a list of worked stations and clears it when the system is deactivated.

## How It Works

### When a QSO is Completed

When you complete a QSO using the "Complete QSO" button in the admin interface, the system:

1. **Stores the caller's information** in a worked callers list including:
   - Callsign (normalized to uppercase)
   - Name (from QRZ lookup)
   - Location/Address (from QRZ lookup)
   - Country (from QRZ lookup)
   - QRZ Image URL (from QRZ lookup)
   - Timestamp when worked
   - First worked timestamp
   - Number of times worked

2. **Handles duplicate contacts** intelligently:
   - If you work the same station multiple times, it updates the existing entry
   - Increments the "times worked" counter
   - Updates the "last worked" timestamp
   - Preserves the "first worked" timestamp

### When System is Deactivated

When you set the system to inactive using the admin panel:

1. **Clears the queue** (existing behavior)
2. **Clears current QSO** (existing behavior)
3. **NEW: Clears worked callers list** - This allows you to start fresh for each activation session

## Database Structure

### Worked Callers Collection

The system creates a new MongoDB collection called `worked_callers` with the following schema:

```javascript
{
  "callsign": "K0TEST",              // Uppercase callsign
  "name": "John Doe",                // Operator name from QRZ
  "location": "Springfield, IL, USA", // Address from QRZ
  "country": "United States",        // DXCC country from QRZ
  "qrz_image": "https://...",        // QRZ photo URL
  "worked_timestamp": "2025-01-...", // Last time worked (ISO format)
  "first_worked": "2025-01-...",     // First time worked (ISO format)
  "times_worked": 2                  // Number of times worked
}
```

## API Endpoints

### Admin Endpoints (Require Authentication)

#### Get Worked Callers
```
GET /api/admin/worked-callers
```
Returns the complete list of worked callers with full details.

#### Clear Worked Callers
```
POST /api/admin/worked-callers/clear
```
Manually clear the worked callers list.

### Public Endpoints

#### Get Worked Callers (Public)
```
GET /api/public/worked-callers
```
Returns the worked callers list for public viewing. Returns empty list if system is inactive.

## Real-time Updates

The system broadcasts worked callers updates via Server-Sent Events (SSE):

- **Event Type**: `worked_callers_update`
- **Triggered When**:
  - QSO is completed (adds to list)
  - System is deactivated (clears list)
  - Admin manually clears list

## Frontend Integration

Frontend applications can:

1. **Subscribe to SSE events** to get real-time updates
2. **Display worked callers** in a dedicated section
3. **Show statistics** like total worked, countries worked, etc.
4. **Filter or search** the worked callers list

## Testing

Use the provided test script to verify functionality:

```bash
python test_worked_callers.py
```

This script tests:
- Adding worked callers
- Handling duplicates
- Counting functionality
- System deactivation clearing

## Benefits

1. **Automatic Logging**: No manual entry required - works with your existing workflow
2. **Duplicate Prevention**: Smart handling of multiple contacts with same station
3. **Rich Information**: Includes QRZ lookup data for each contact
4. **Clean State**: Automatically clears for each session
5. **Real-time Updates**: Frontend stays synchronized automatically
6. **Public Visibility**: Visitors can see your session activity

## Migration

This is a non-breaking change:
- Existing functionality continues to work unchanged
- New collection is created automatically when first used
- No data migration required
- Can be enabled/disabled by simply using or not using the Complete QSO feature

## Future Enhancements

Potential future features could include:
- Export worked callers to ADIF format
- Statistics and charts
- Integration with contest logging
- Duplicate checking against external logs
