# Cloud Functions Deployment Script
# Usage: .\deploy.ps1

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectId = "smarttanpaku-ltv-dev",
    
    [Parameter(Mandatory=$false)]
    [string]$BucketName = "smarttanpaku-ltv-dev-raw-jsons",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "asia-northeast1",
    
    [Parameter(Mandatory=$false)]
    [string]$BqDataset = "rakuten_orders",
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Cloud Functions Deployment Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Display configuration
Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Project ID: $ProjectId"
Write-Host "  Bucket Name: $BucketName"
Write-Host "  Region: $Region"
Write-Host "  BQ Dataset: $BqDataset"
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN Mode] Will not actually deploy" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Command to be executed:" -ForegroundColor Green
    Write-Host "gcloud functions deploy rakuten-etl \"
    Write-Host "  --gen2 \"
    Write-Host "  --runtime=python311 \"
    Write-Host "  --region=$Region \"
    Write-Host "  --source=. \"
    Write-Host "  --entry-point=main \"
    Write-Host "  --trigger-http \"
    Write-Host "  --allow-unauthenticated \"
    Write-Host "  --memory=2GiB \"
    Write-Host "  --timeout=540s \"
    Write-Host "  --set-env-vars=`"PROJECT_ID=$ProjectId,BUCKET_NAME=$BucketName,BQ_DATASET=$BqDataset,BQ_LOCATION=$Region,SKIP_LTV_UPDATE=false`""
    Write-Host ""
    exit 0
}

# Confirmation
Write-Host "Do you want to start deployment with the above settings? (y/n): " -ForegroundColor Yellow -NoNewline
$confirmation = Read-Host
if ($confirmation -ne 'y') {
    Write-Host "Deployment cancelled" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting deployment..." -ForegroundColor Green
Write-Host ""

# Execute deployment command
gcloud functions deploy rakuten-etl `
  --gen2 `
  --runtime=python311 `
  --region=$Region `
  --source=. `
  --entry-point=main `
  --trigger-http `
  --allow-unauthenticated `
  --memory=2GiB `
  --timeout=540s `
  --set-env-vars="PROJECT_ID=$ProjectId,BUCKET_NAME=$BucketName,BQ_DATASET=$BqDataset,BQ_LOCATION=$Region,SKIP_LTV_UPDATE=false,PRODUCT_MASTER_SHEET_ID=1Tp4SdNR8EJumFkrYyVYbnKCWCYw18s-3K9B_YqYAKPo" `
  --project=$ProjectId

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Deployment completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Check deployment status in Cloud Console"
    Write-Host "2. Test execution (DRY RUN)"
    $functionUrl = "https://$Region-$ProjectId.cloudfunctions.net/rakuten-etl"
    Write-Host "   Test URL: $functionUrl"
    Write-Host '   Invoke-WebRequest -Uri "' + $functionUrl + '?mode=MONTHLY&dry_run=1"'
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "Deployment failed" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Check gcloud authentication: gcloud auth list"
    Write-Host "2. Check project configuration: gcloud config get-value project"
    Write-Host "3. See DEPLOYMENT_GUIDE.md for details"
    Write-Host ""
    exit 1
}
