$ErrorActionPreference = 'Stop'

$tshark = $null
$candidates = @(
    'C:\Program Files\Wireshark\tshark.exe',
    'C:\Program Files (x86)\Wireshark\tshark.exe'
)
foreach ($c in $candidates) {
    if (Test-Path $c) { $tshark = $c; break }
}
if (-not $tshark) {
    $cmd = Get-Command tshark.exe -ErrorAction SilentlyContinue
    if ($cmd) { $tshark = $cmd.Source }
}
if (-not $tshark) {
    Write-Error "tshark.exe not found. Install Wireshark (with Npcap loopback support) from https://www.wireshark.org"
    exit 1
}
Write-Host "Using tshark: $tshark" -ForegroundColor Cyan

$ifaceEnv = $env:IF
if ($ifaceEnv) {
    $iface = $ifaceEnv
} else {

    $list = & $tshark -D 2>$null
    $loop = $list | Where-Object { $_ -match 'oopback' } | Select-Object -First 1
    if (-not $loop) {
        Write-Error "No loopback interface found. Re-run Npcap installer and enable 'Support loopback traffic'. Run '$tshark -D' to list interfaces."
        exit 1
    }

    if ($loop -match '^\s*(\d+)\.\s') { $iface = $Matches[1] }
    else { $iface = ($loop -split '\s')[1] }
    Write-Host "Auto-detected loopback: $loop" -ForegroundColor Cyan
}
Write-Host "Using interface: $iface" -ForegroundColor Cyan

$BasePort = if ($env:BASE_PORT) { [int]$env:BASE_PORT } else { 49200 }
$Out      = 'tshark_totals.csv'
$PcapDir  = 'pcaps'
if (-not (Test-Path $PcapDir)) { New-Item -ItemType Directory -Path $PcapDir | Out-Null }

$Phases = @(
    @{ Row=4;  Name='Registration_User-Issuer' },
    @{ Row=5;  Name='Registration_Issuer-User' },
    @{ Row=6;  Name='Session_User-Verifier' },
    @{ Row=7;  Name='Session_Verifier-User' },
    @{ Row=8;  Name='Request_User-Verifier' },
    @{ Row=9;  Name='Request_Verifier-User' },
    @{ Row=10; Name='Aggregation_Verifier-Chain' },
    @{ Row=11; Name='Revocation_Issuer-Chain' },
    @{ Row=12; Name='PRE_delegate' },
    @{ Row=13; Name='PRE_request' },
    @{ Row=14; Name='IPFS_put' },
    @{ Row=15; Name='IPFS_get' }
)

"sheet_row,phase,bytes_on_wire_total" | Out-File -FilePath $Out -Encoding ASCII

foreach ($p in $Phases) {
    $row  = $p.Row
    $name = $p.Name
    $port = $BasePort + $row - 4
    $pcap = Join-Path $PcapDir ("row{0}_{1}.pcap" -f $row, $name)

    Write-Host ("[row {0}] capturing {1} on iface={2} port={3} -> {4}" -f $row,$name,$iface,$port,$pcap) -ForegroundColor Yellow

    if (Test-Path $pcap) { Remove-Item $pcap -Force }
    $pcapAbs = (Resolve-Path $PcapDir).Path + '\' + (Split-Path $pcap -Leaf)
    $job = Start-Job -ScriptBlock {
        param($t, $i, $p, $f)
        & $t -i $i -f "tcp port $p" -w $f 2>&1
    } -ArgumentList $tshark, $iface, $port, $pcapAbs

    $null = Wait-Job $job -Timeout 15
    Stop-Job $job -ErrorAction SilentlyContinue | Out-Null
    $jobOut = Receive-Job $job -ErrorAction SilentlyContinue 2>&1
    Remove-Job $job -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 800
    if (-not (Test-Path $pcapAbs)) {
        Write-Host ("    WARN: pcap missing. tshark output: {0}" -f ($jobOut -join ' | ')) -ForegroundColor Red
        "$row,$name,0" | Out-File -FilePath $Out -Append -Encoding ASCII
        continue
    }
    $pcap = $pcapAbs

    $stat  = & $tshark -r $pcap -q -z io,stat,0 2>$null
    $total = 0

    $dataLine = $stat | Where-Object { $_ -match '\|\s*\d+\s*<>' } | Select-Object -First 1
    if ($dataLine) {
        $cols = ($dataLine -split '\|') | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
        if ($cols.Count -ge 3) { $total = [int64]$cols[-1] }
    }
    Write-Host ("    total bytes = {0}" -f $total)
    "$row,$name,$total" | Out-File -FilePath $Out -Append -Encoding ASCII
}

Write-Host ""
Write-Host "Done. CSV -> $Out   PCAPs -> $PcapDir\" -ForegroundColor Green
Write-Host "Paste target: sheet 05_Communication, column E (With headers) rows 4..15." -ForegroundColor Green
