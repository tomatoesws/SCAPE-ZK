param(
    [int]$Minutes = 4,
    [string]$Python = "C:\Users\Jay\AppData\Local\Microsoft\WindowsApps\python3.11.exe",
    [string]$Host_ = "127.0.0.1"
)

$end = (Get-Date).AddMinutes($Minutes)
$iter = 0
Write-Host "Traffic loop: running until $end ($Minutes min). Ctrl+C to stop." -ForegroundColor Cyan
while ((Get-Date) -lt $end) {
    $iter++
    & $Python .\e2e_harness.py --host $Host_ --runs 1 --out "_loop_scratch.csv" 2>$null | Out-Null
    if ($iter % 50 -eq 0) {
        $remaining = [int]($end - (Get-Date)).TotalSeconds
        Write-Host ("  iter {0}  ({1}s remaining)" -f $iter, $remaining) -ForegroundColor DarkGray
    }
}
Write-Host ("Done. {0} harness iterations in {1} min." -f $iter, $Minutes) -ForegroundColor Green
