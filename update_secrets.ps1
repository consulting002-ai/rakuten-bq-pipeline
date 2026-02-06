# Secret Manager APIキー更新スクリプト
# Usage: .\update_secrets.ps1

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectId = "smarttanpaku-ltv-dev",
    
    [Parameter(Mandatory=$false)]
    [string]$ServiceSecretId = "rakuten-service-secret",
    
    [Parameter(Mandatory=$false)]
    [string]$LicenseKeyId = "rakuten-license-key",
    
    [Parameter(Mandatory=$false)]
    [switch]$ListOnly
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Secret Manager APIキー更新スクリプト" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 設定の表示
Write-Host "設定:" -ForegroundColor Yellow
Write-Host "  Project ID: $ProjectId"
Write-Host "  Service Secret ID: $ServiceSecretId"
Write-Host "  License Key ID: $LicenseKeyId"
Write-Host ""

# Secret一覧を表示
if ($ListOnly) {
    Write-Host "既存のSecret一覧:" -ForegroundColor Green
    gcloud secrets list --project=$ProjectId
    Write-Host ""
    Write-Host "$ServiceSecretId のバージョン:" -ForegroundColor Green
    gcloud secrets versions list $ServiceSecretId --project=$ProjectId
    Write-Host ""
    Write-Host "$LicenseKeyId のバージョン:" -ForegroundColor Green
    gcloud secrets versions list $LicenseKeyId --project=$ProjectId
    exit 0
}

Write-Host "⚠️  このスクリプトはAPIキーを更新します" -ForegroundColor Yellow
Write-Host "⚠️  新しい値を一時ファイルに保存します（実行後は自動削除）" -ForegroundColor Yellow
Write-Host ""

# 確認
Write-Host "続行しますか？ (y/n): " -ForegroundColor Yellow -NoNewline
$confirmation = Read-Host
if ($confirmation -ne 'y') {
    Write-Host "更新をキャンセルしました" -ForegroundColor Red
    exit 1
}

Write-Host ""

# SERVICE_SECRETの更新
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SERVICE_SECRET の更新" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "新しい SERVICE_SECRET を入力してください: " -ForegroundColor Yellow -NoNewline
$serviceSecret = Read-Host -AsSecureString
$serviceSecretPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($serviceSecret)
)

if ([string]::IsNullOrWhiteSpace($serviceSecretPlain)) {
    Write-Host "エラー: SERVICE_SECRET が入力されていません" -ForegroundColor Red
    exit 1
}

# 一時ファイルに保存
$tempServiceFile = "temp_service_secret_$(Get-Random).txt"
Set-Content -Path $tempServiceFile -Value $serviceSecretPlain -NoNewline

Write-Host "SERVICE_SECRET を更新中..." -ForegroundColor Green
gcloud secrets versions add $ServiceSecretId `
  --data-file=$tempServiceFile `
  --project=$ProjectId

if ($LASTEXITCODE -ne 0) {
    Write-Host "エラー: SERVICE_SECRET の更新に失敗しました" -ForegroundColor Red
    Remove-Item $tempServiceFile -ErrorAction SilentlyContinue
    exit 1
}

# 一時ファイルを削除
Remove-Item $tempServiceFile
Write-Host "✓ SERVICE_SECRET を更新しました" -ForegroundColor Green
Write-Host ""

# LICENSE_KEYの更新
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LICENSE_KEY の更新" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "新しい LICENSE_KEY を入力してください: " -ForegroundColor Yellow -NoNewline
$licenseKey = Read-Host -AsSecureString
$licenseKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($licenseKey)
)

if ([string]::IsNullOrWhiteSpace($licenseKeyPlain)) {
    Write-Host "エラー: LICENSE_KEY が入力されていません" -ForegroundColor Red
    exit 1
}

# 一時ファイルに保存
$tempLicenseFile = "temp_license_key_$(Get-Random).txt"
Set-Content -Path $tempLicenseFile -Value $licenseKeyPlain -NoNewline

Write-Host "LICENSE_KEY を更新中..." -ForegroundColor Green
gcloud secrets versions add $LicenseKeyId `
  --data-file=$tempLicenseFile `
  --project=$ProjectId

if ($LASTEXITCODE -ne 0) {
    Write-Host "エラー: LICENSE_KEY の更新に失敗しました" -ForegroundColor Red
    Remove-Item $tempLicenseFile -ErrorAction SilentlyContinue
    exit 1
}

# 一時ファイルを削除
Remove-Item $tempLicenseFile
Write-Host "✓ LICENSE_KEY を更新しました" -ForegroundColor Green
Write-Host ""

# 完了
Write-Host "========================================" -ForegroundColor Green
Write-Host "APIキーの更新が完了しました！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "次のステップ:" -ForegroundColor Yellow
Write-Host "1. 更新されたバージョンを確認:"
Write-Host "   gcloud secrets versions list $ServiceSecretId --project=$ProjectId"
Write-Host "2. Cloud Functions を再デプロイ（新しいSecretを使用するため）:"
Write-Host "   .\deploy.ps1"
Write-Host ""
