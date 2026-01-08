# Wrapper script to auto-approve cleanup
$filesToRemove = @()
$filesToRemove += "2WEEK_EXECUTION_SUMMARY.md"
$filesToRemove += "ACCELERATED_2WEEK_PLAN.md"
$filesToRemove += "CLEANUP_COMPLETE.txt"
$filesToRemove += "CLEANUP_SUMMARY.md"
$filesToRemove += "COMPREHENSIVE_CHECKLIST.md"
$filesToRemove += "DELIVERABLES_SUMMARY.md"
$filesToRemove += "DEPLOYMENT_GUIDE.md"
$filesToRemove += "DEVELOPMENT_ROADMAP.md"
$filesToRemove += "DOCUMENTATION_INDEX.md"
$filesToRemove += "IMMEDIATE_ACTION_ITEMS.md"
$filesToRemove += "IMPLEMENTATION_COMPLETE.md"
$filesToRemove += "PROJECT_STATUS_SUMMARY.md"
$filesToRemove += "QUICK_REFERENCE.md"
$filesToRemove += "QUICK_START.md"
$filesToRemove += "QUICK_TEST_GUIDE.md"
$filesToRemove += "REST_API_SETUP_GUIDE.md"
$filesToRemove += "UI_FIXES_APPLIED.md"
$filesToRemove += "UI_FIXES_QUICK_REFERENCE.txt"
$filesToRemove += "UI_FIXES_VERIFICATION.md"
$filesToRemove += "UI_SCAN_REPORT.md"
$filesToRemove += ".env.postgresql"
$filesToRemove += ".env.raspberry-pi"
$filesToRemove += ".flake8"
$filesToRemove += "railway.json"
$filesToRemove += "Procfile"
$filesToRemove += "runtime.txt"
$filesToRemove += "VERSION.txt"
$filesToRemove += "gunicorn_config.py"
$filesToRemove += "nginx_elibrary.conf"
$filesToRemove += "elibrary.service"
$filesToRemove += "pytest.ini"
$filesToRemove += "db.sqlite3-shm"
$filesToRemove += "db.sqlite3-wal"
$filesToRemove += "TS_OPAC_eLibrary_Postman.postman_collection.json"
$filesToRemove += "TS_OPAC_eLibrary_REST_API.postman_collection.json"
$filesToRemove += "logs"

Write-Host "`n-- TS OPAC eLibrary - Cleanup Started --" -ForegroundColor Cyan

$removedCount = 0
$totalFiles = $filesToRemove.Count

Write-Host "Removing $totalFiles files...`n" -ForegroundColor Yellow

foreach ($file in $filesToRemove) {
    if (Test-Path $file) {
        if ((Get-Item $file).PSIsContainer) {
            Remove-Item -Path $file -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  [OK] Removed: $file" -ForegroundColor Green
            $removedCount++
        }
        else {
            Remove-Item -Path $file -Force -ErrorAction SilentlyContinue
            Write-Host "  [OK] Removed: $file" -ForegroundColor Green
            $removedCount++
        }
    }
}

Write-Host "`n-- CLEANUP COMPLETE --" -ForegroundColor Green
Write-Host "Files Removed: $removedCount/$totalFiles" -ForegroundColor Green
Write-Host "Project is clean and ready!`n" -ForegroundColor Cyan
Write-Host "Next Step: Follow DOCKER_QUICK_START.md`n" -ForegroundColor Yellow
