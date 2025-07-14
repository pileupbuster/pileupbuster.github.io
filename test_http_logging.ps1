# Test HTTP POST integration for Pileup Buster logging software
# Usage: .\test_http_logging.ps1 EI6LF 14.2715 SSB

param(
    [Parameter(Mandatory=$true)]
    [string]$Callsign,
    
    [Parameter(Mandatory=$false)]
    [double]$FrequencyMHz,
    
    [Parameter(Mandatory=$false)]
    [string]$Mode,
    
    [Parameter(Mandatory=$false)]
    [string]$BackendUrl = "http://localhost:8000"
)

# Create the message in the same format as your logging software
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")

$message = @{
    type = "qso_start"
    data = @{
        callsign = $Callsign
        frequency_mhz = $FrequencyMHz
        mode = $Mode
        source = "pblog_native"
        timestamp = $timestamp
        triggered_by = "callsign_finalized"
    }
} | ConvertTo-Json -Depth 3

$url = "$BackendUrl/api/admin/qso/logging-direct"

Write-Host "📤 Sending QSO start for $Callsign..." -ForegroundColor Green
Write-Host "🌐 URL: $url" -ForegroundColor Cyan
Write-Host "📋 Message:" -ForegroundColor Yellow
Write-Host $message -ForegroundColor White
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri $url -Method POST -Body $message -ContentType "application/json" -TimeoutSec 10
    
    Write-Host "✅ SUCCESS! QSO started successfully" -ForegroundColor Green
    Write-Host "📋 Response:" -ForegroundColor Yellow
    Write-Host ($response | ConvertTo-Json -Depth 5) -ForegroundColor White
    
    if ($response.qso_started) {
        Write-Host ""
        Write-Host "🎉 QSO Details:" -ForegroundColor Green
        Write-Host "   Callsign: $($response.qso_started.callsign)" -ForegroundColor White
        Write-Host "   Source: $($response.qso_started.source)" -ForegroundColor White
        Write-Host "   Was in queue: $($response.qso_started.was_in_queue)" -ForegroundColor White
        Write-Host "   Frequency: $($response.qso_started.frequency_mhz) MHz" -ForegroundColor White
        Write-Host "   Mode: $($response.qso_started.mode)" -ForegroundColor White
    }
}
catch {
    Write-Host "❌ ERROR: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode
        Write-Host "📡 Status Code: $statusCode" -ForegroundColor Red
        
        try {
            $errorStream = $_.Exception.Response.GetResponseStream()
            $reader = New-Object System.IO.StreamReader($errorStream)
            $errorBody = $reader.ReadToEnd()
            Write-Host "📋 Error Details: $errorBody" -ForegroundColor Red
        }
        catch {
            Write-Host "📋 Could not read error details" -ForegroundColor Red
        }
    }
    
    if ($_.Exception.Message -like "*ConnectFailure*") {
        Write-Host "💡 Make sure your backend is running on $BackendUrl" -ForegroundColor Yellow
    }
}
