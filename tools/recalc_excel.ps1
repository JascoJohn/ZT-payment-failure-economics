# Recalculate an .xlsx with Microsoft Excel (Windows), count formula errors on every sheet, and save the values into the file.
#   powershell -File tools\recalc_excel.ps1 -Path outputs\payment_failure_analysis.xlsx -Out outputs\intermediate\recalc_report.json
param([Parameter(Mandatory=$true)][string]$Path, [Parameter(Mandatory=$true)][string]$Out)
$full = (Resolve-Path $Path).Path
$xl = New-Object -ComObject Excel.Application
$xl.Visible = $false
$xl.DisplayAlerts = $false
$xl.Calculation = -4135                      # manual while opening
$wb = $xl.Workbooks.Open($full, 0)
$sw = [Diagnostics.Stopwatch]::StartNew()
$xl.CalculateFullRebuild()
$secs = [math]::Round($sw.Elapsed.TotalSeconds)
$errors = [ordered]@{}
foreach ($ws in $wb.Worksheets) {
    $n = 0
    try { $n = $ws.UsedRange.SpecialCells(-4123, 16).Count } catch { $n = 0 }     # formulas that return an error
    $errors[$ws.Name] = $n
}
$xl.Calculation = -4105                      # back to automatic
$wb.Save()
$wb.Close($false)
$xl.Quit()
[void][Runtime.InteropServices.Marshal]::ReleaseComObject($xl)
[ordered]@{ engine = "Microsoft Excel"; seconds = $secs; errors = $errors } | ConvertTo-Json | Set-Content -Path $Out -Encoding UTF8
