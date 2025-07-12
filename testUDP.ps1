# Create a UDP listener script
$listener = New-Object System.Net.Sockets.UdpClient(2237)
$endpoint = New-Object System.Net.IPEndPoint([System.Net.IPAddress]::Any, 2237)

Write-Host "Listening for UDP packets on port 2237..."
Write-Host "Press Ctrl+C to stop"

try {
    while ($true) {
        $data = $listener.Receive([ref]$endpoint)
        $message = [System.Text.Encoding]::UTF8.GetString($data)
        Write-Host "Received from $($endpoint.Address):$($endpoint.Port) - $message"
    }
}
finally {
    $listener.Close()
}