# Project Cleanup Script
# This script removes unnecessary files and keeps only essential ones

Write-Host "`n`n🧹 TS OPAC eLibrary - Project Cleanup" -ForegroundColor Cyan
Write-Host "====================================`n" -ForegroundColor Cyan

# List of files/patterns to REMOVE (not essential)
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

# List of files/folders to KEEP (essential)
$filesToKeep = @()
$filesToKeep += "manage.py"
$filesToKeep += "requirements.txt"
$filesToKeep += "db.sqlite3"
$filesToKeep += "accounts"
$filesToKeep += "api"
$filesToKeep += "catalog"
$filesToKeep += "circulation"
$filesToKeep += "elibrary"
$filesToKeep += "media"
$filesToKeep += "static"
$filesToKeep += "templates"
$filesToKeep += ".env"
$filesToKeep += ".env.example"
$filesToKeep += ".env.production"
$filesToKeep += ".gitignore"
$filesToKeep += ".git"
$filesToKeep += ".vscode"
$filesToKeep += "Dockerfile"
$filesToKeep += "docker-compose.yml"
$filesToKeep += "nginx.conf"
$filesToKeep += "elibrary-gunicorn.service"
$filesToKeep += "elibrary-nginx.service"
$filesToKeep += "README.md"
$filesToKeep += "DOCKER_WINDOWS_SETUP.md"
$filesToKeep += "DOCKER_QUICK_START.md"
$filesToKeep += "DAYS_1-2_COMPLETION_REPORT.md"
$filesToKeep += "DAYS_3-4_DEPLOYMENT_GUIDE.md"
$filesToKeep += "migrate_to_postgres.py"
$filesToKeep += "venv"
$filesToKeep += "TS_OPAC_eLibrary.postman_collection.json"

Write-Host "📋 FILES TO REMOVE:" -ForegroundColor Yellow
foreach ($file in $filesToRemove) {
    $path = Join-Path -Path "." -ChildPath $file
    if (Test-Path $path) {
        Write-Host "  ❌ $file" -ForegroundColor Red
    }
}

Write-Host "`n✅ FILES TO KEEP:" -ForegroundColor Green
foreach ($file in $filesToKeep) {
    if (Test-Path $file) {
        if ((Get-Item $file).PSIsContainer) {
            Write-Host "  📁 $file/" -ForegroundColor Green
        } else {
            Write-Host "  📄 $file" -ForegroundColor Green
        }
    }
}

Write-Host "`n" -ForegroundColor Yellow
$proceed = Read-Host "Proceed with cleanup? (yes/no)"

if ($proceed -eq "yes") {
    $removedCount = 0
    $skippedCount = 0
    
    Write-Host "`nRemoving files..." -ForegroundColor Cyan
    
    foreach ($file in $filesToRemove) {
        $path = Join-Path -Path "." -ChildPath $file
        if (Test-Path $path) {
            try {
                if ((Get-Item $path).PSIsContainer) {
                    Remove-Item -Path $path -Recurse -Force
                } else {
                    Remove-Item -Path $path -Force
                }
                Write-Host "  ✓ Removed: $file" -ForegroundColor Green
                $removedCount++
            } catch {
                Write-Host "  ⚠ Failed to remove: $file" -ForegroundColor Yellow
                $skippedCount++
            }
        }
    }
    
    Write-Host "`n" -ForegroundColor Cyan
    Write-Host "╔════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║   CLEANUP COMPLETE!                ║" -ForegroundColor Cyan
    Write-Host "╠════════════════════════════════════╣" -ForegroundColor Cyan
    Write-Host "║  Files Removed: $removedCount" -ForegroundColor Green
    Write-Host "║  Skipped: $skippedCount" -ForegroundColor Yellow
    Write-Host "║  Project is now clean! ✨          ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════╝" -ForegroundColor Cyan
    
} else {
    Write-Host "`n⛔ Cleanup cancelled." -ForegroundColor Yellow
}

Write-Host "`n✅ Next: Run DOCKER_QUICK_START.md`n" -ForegroundColor Cyan
