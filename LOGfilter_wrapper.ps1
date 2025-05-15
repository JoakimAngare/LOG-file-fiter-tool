# LOGfilter_wrapper.ps1
# PowerShell wrapper for the LOGfilter_enhanced.py script

param (
    [Parameter(HelpMessage="Directory containing LOG files and/or ZIP files")]
    [string]$Directory = ".",

    [Parameter(HelpMessage="Prefix for output files")]
    [string]$OutputPrefix = "filtered_log_results",

    [Parameter(HelpMessage="Configuration file path")]
    [string]$ConfigFile = "log_filter_config.json",

    [Parameter(HelpMessage="Create a default configuration file and exit")]
    [switch]$CreateConfig,

    [Parameter(HelpMessage="Skip processing ZIP files")]
    [switch]$NoZip,

    [Parameter(HelpMessage="Display help information")]
    [switch]$Help
)

# Function to display help
function Show-Help {
    Write-Host "LOGfilter PowerShell Wrapper"
    Write-Host "This script runs the LOGfilter_enhanced.py Python script to filter and highlight content in LOG files."
    Write-Host ""
    Write-Host "Parameters:"
    Write-Host "  -Directory      : Directory containing LOG files and/or ZIP files (default: current directory)"
    Write-Host "  -OutputPrefix   : Prefix for output files (default: filtered_log_results)"
    Write-Host "  -ConfigFile     : Configuration file path (default: log_filter_config.json)"
    Write-Host "  -CreateConfig   : Create a default configuration file and exit"
    Write-Host "  -NoZip          : Skip processing ZIP files"
    Write-Host "  -Help           : Display this help information"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\LOGfilter_wrapper.ps1"
    Write-Host "  .\LOGfilter_wrapper.ps1 -Directory 'C:\Logs' -OutputPrefix 'my_results'"
    Write-Host "  .\LOGfilter_wrapper.ps1 -CreateConfig"
    Write-Host "  .\LOGfilter_wrapper.ps1 -NoZip"
}

# Show help if requested
if ($Help) {
    Show-Help
    exit
}

# Find the Python script in the current directory
$ScriptDir = $PSScriptRoot
$PythonScript = Join-Path -Path $ScriptDir -ChildPath "LOGfilter_enhanced.py"

# Check if the Python script exists
if (-not (Test-Path $PythonScript)) {
    Write-Error "Error: Could not find the Python script at $PythonScript"
    Write-Host "Please make sure the LOGfilter_enhanced.py file is in the same directory as this PowerShell script."
    exit 1
}

# Try to find Python
$PythonCommand = "python"
try {
    # Check if Python is available
    $null = & $PythonCommand --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python command not found"
    }
} catch {
    # Try python3 as an alternative
    $PythonCommand = "python3"
    try {
        $null = & $PythonCommand --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Python is not available. Please install Python or make sure it's in your PATH."
            exit 1
        }
    } catch {
        Write-Error "Python is not available. Please install Python or make sure it's in your PATH."
        exit 1
    }
}

# Create a temporary batch file to handle spaces in paths
$BatchFile = Join-Path -Path $env:TEMP -ChildPath "run_logfilter_$([Guid]::NewGuid().ToString()).bat"

# Build the command with proper quotes for the batch file
$BatchCommand = "@echo off`r`n"
$BatchCommand += "cd /d `"$ScriptDir`"`r`n"
$BatchCommand += "$PythonCommand `"$PythonScript`""

# Add arguments to the batch command
if (-not [string]::IsNullOrEmpty($Directory)) {
    $BatchCommand += " -d `"$Directory`""
}

if (-not [string]::IsNullOrEmpty($OutputPrefix)) {
    $BatchCommand += " -o `"$OutputPrefix`""
}

if (-not [string]::IsNullOrEmpty($ConfigFile)) {
    $BatchCommand += " -c `"$ConfigFile`""
}

if ($CreateConfig) {
    $BatchCommand += " --create-config"
}

if ($NoZip) {
    $BatchCommand += " --no-zip"
}

# Write the batch file
Set-Content -Path $BatchFile -Value $BatchCommand

# Display the command that will be executed
Write-Host "Executing: $($BatchCommand.Replace("`r`n", " "))" -ForegroundColor Cyan

try {
    # Run the batch file
    $Process = Start-Process -FilePath $BatchFile -NoNewWindow -PassThru -Wait
    
    # Clean up the temporary batch file
    if (Test-Path $BatchFile) {
        Remove-Item -Path $BatchFile -Force
    }
    
    if ($Process.ExitCode -ne 0) {
        Write-Host "The Python script exited with code $($Process.ExitCode)" -ForegroundColor Red
        exit $Process.ExitCode
    }
    
    # Success message if the script ran without errors
    Write-Host "`nLOG file filtering completed successfully!" -ForegroundColor Green
    
    # Open the output files if they exist
    $HTMLOutput = Join-Path -Path $ScriptDir -ChildPath "$OutputPrefix.html"
    if (Test-Path $HTMLOutput) {
        Write-Host "`nWould you like to open the HTML results? (Y/N)" -ForegroundColor Yellow
        $Response = Read-Host
        if ($Response -eq "Y" -or $Response -eq "y") {
            Start-Process $HTMLOutput
        }
    }
    
} catch {
    Write-Error "Error executing the script: $_"
    
    # Clean up the temporary batch file in case of error
    if (Test-Path $BatchFile) {
        Remove-Item -Path $BatchFile -Force
    }
    
    exit 1
}