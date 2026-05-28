# monitor_serial.ps1 -- PowerShell script to log serial port data
# PEEKDOCS_TEST_MARKER

param(
    [string]$PortName = "COM3",
    [int]$BaudRate = 115200,
    [string]$LogFile = "serial_log.csv"
)

Write-Host "Opening $PortName at $BaudRate baud..."

$port = New-Object System.IO.Ports.SerialPort $PortName, $BaudRate, "None", 8, "One"
$port.ReadTimeout = 2000

try {
    $port.Open()
    "Timestamp,RawData" | Out-File -FilePath $LogFile

    while ($true) {
        try {
            $line = $port.ReadLine()
            $entry = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss.fff'),$line"
            $entry | Tee-Object -FilePath $LogFile -Append
        }
        catch [System.TimeoutException] {
            Write-Verbose "Read timeout, retrying..."
        }
    }
}
finally {
    if ($port.IsOpen) { $port.Close() }
    Write-Host "Port closed."
}
