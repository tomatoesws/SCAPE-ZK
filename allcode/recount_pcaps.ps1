$ErrorActionPreference = 'Stop'

$tshark = $null
$candidates = @(
    'D:\study random\Wireshark\tshark.exe',
    'C:\Program Files\Wireshark\tshark.exe',
    'C:\Program Files (x86)\Wireshark\tshark.exe'
)
foreach ($c in $candidates) { if (Test-Path $c) { $tshark = $c; break } }
if (-not $tshark) {
    $cmd = Get-Command tshark.exe -ErrorAction SilentlyContinue
    if ($cmd) { $tshark = $cmd.Source }
}
if (-not $tshark) { Write-Error "tshark not found"; exit 1 }
Write-Host "Using tshark: $tshark" -ForegroundColor Cyan

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

$Out = 'tshark_totals.csv'
"sheet_row,phase,bytes_on_wire_total" | Out-File -FilePath $Out -Encoding ASCII

foreach ($p in $Phases) {
    $row = $p.Row; $name = $p.Name
    $pcap = Join-Path 'pcaps' ("row{0}_{1}.pcap" -f $row, $name)
    if (-not (Test-Path $pcap)) {
        Write-Host ("[row {0}] MISSING {1}" -f $row, $pcap) -ForegroundColor Red
        "$row,$name,0" | Out-File -FilePath $Out -Append -Encoding ASCII
        continue
    }

    $frameLens = & $tshark -r $pcap -T fields -e frame.len 2>$null
    $total = 0
    foreach ($l in $frameLens) {
        if ($l -and $l -match '^\d+$') { $total += [int64]$l }
    }
    $nPackets = ($frameLens | Where-Object { $_ -match '^\d+$' }).Count
    Write-Host ("[row {0}] {1,-32} packets={2,5}  bytes={3}" -f $row, $name, $nPackets, $total)
    "$row,$name,$total" | Out-File -FilePath $Out -Append -Encoding ASCII
}

Write-Host ""
Write-Host "Done. CSV -> $Out" -ForegroundColor Green
Write-Host "Paste target: sheet 05_Communication, column E rows 4..15." -ForegroundColor Green
