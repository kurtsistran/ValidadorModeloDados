<#
.SYNOPSIS
    Gera o executável (PyInstaller) e o instalador (Inno Setup) do MVP local.
.DESCRIPTION
    Use um ambiente limpo criado a partir de requirements-dev.lock e
    packaging/requirements-build.lock. Nenhum arquivo de exemplo ou confidencial
    entra no pacote: só o código em src/ e rules/default_rules.yaml.
#>
param(
    [string]$Python = ".build-venv\Scripts\python.exe",
    [string]$Iscc = "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path $Python)) { throw "Python de build não encontrado: $Python" }
if (-not (Test-Path $Iscc)) { throw "ISCC.exe não encontrado: $Iscc" }

$version = & $Python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])"
$app = Join-Path $root "dist\DataModelAuditor"

# Remove somente as saídas de build anteriores.
foreach ($old in @($app, (Join-Path $root "build\pyinstaller"))) {
    if (Test-Path $old) { Remove-Item -Recurse -Force $old }
}

& $Python -m PyInstaller packaging\data_model_auditor.spec --noconfirm --clean `
    --distpath dist --workpath build\pyinstaller
if ($LASTEXITCODE -ne 0) { throw "PyInstaller falhou." }

New-Item -ItemType Directory -Force (Join-Path $app "rules") | Out-Null
Copy-Item rules\default_rules.yaml (Join-Path $app "rules\default_rules.yaml")

$smoke = Start-Process (Join-Path $app "DataModelAuditor.exe") -ArgumentList "--smoke-test" -Wait -PassThru
if ($smoke.ExitCode -ne 0) { throw "Smoke test do executável falhou: código $($smoke.ExitCode)." }

& $Iscc "/DAppVersion=$version" packaging\installer.iss
if ($LASTEXITCODE -ne 0) { throw "Inno Setup falhou." }

Write-Host "Instalador gerado em dist\installer\DataModelAuditor-Setup-$version.exe"
