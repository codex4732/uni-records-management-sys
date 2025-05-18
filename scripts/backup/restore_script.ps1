<#
.SYNOPSIS
    MySQL Restore Script with Decryption
.DESCRIPTION
    This script identifies the most recent MySQL database backup, decrypts it using OpenSSL, and performs a database restore.
.NOTES
    Original work from: https://github.com/kn-msccs-uol/collegedatabasesystem
    Originally licensed under MIT. Relicensed under BSD 3-Clause with permission
    from original author. Significant modifications made for uni-records-management-sys.
#>

# Configuration
$config = @{
    MySQLPath = "C:\Program Files\MySQL\MySQL Server 9.3\bin\mysql.exe"
    OpenSSLPath = "C:\Program Files\Git\usr\bin\openssl.exe"
    DBUser = "root"
    DBName = "urms_dev"
    BackupDir = "C:\DBBackups\urms_dev"
    TimeStampFormat = 'yyyyMMdd_HHmmss'
}

# Derived paths and values
$config.LogsDir = Join-Path $config.BackupDir "logs"
$timestamp = Get-Date -Format $config.TimeStampFormat
$logFile = Join-Path $config.LogsDir "restore_$timestamp.log"

# Logging function (output to console and log file)
function Write-Log {
    param($Message)
    try {
        $logMessage = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss'): $Message"
        Write-Host $logMessage
        Add-Content -Path $logFile -Value $logMessage -ErrorAction Stop
    } catch {
        Write-Error "Failed to activate log writing function: $_"
    }
}

# Function to validate paths and create directories
function Initialize-RestoreEnvironment {
    param (
        [hashtable]$Config
    )
    
    # Validate required paths
    $requiredPaths = @{
        MySQL = $Config.MySQLPath
        OpenSSL = $Config.OpenSSLPath
    }

    foreach ($path in $requiredPaths.GetEnumerator()) {
        if (!(Test-Path $path.Value)) {
            Write-Host "$($path.Key) not found at $($path.Value)"
            return $false
        }
    }

    # Create logs directory if it doesn't exist
    if (!(Test-Path $Config.LogsDir)) {
        try {
            New-Item -ItemType Directory -Path $Config.LogsDir -ErrorAction Stop | Out-Null
            Write-Host "Created directory: $($Config.LogsDir)"
        } catch {
            Write-Host "Failed to create logs directory: $_"
            return $false
        }
    }

    # Validate backup directory exists
    if (!(Test-Path $Config.BackupDir)) {
        Write-Host "Backup directory not found: $($Config.BackupDir)"
        return $false
    }

    return $true
}

# Function to find the most recent backup file
function Get-LatestBackup {
    param (
        [string]$BackupDir
    )
    
    try {
        $latestBackup = Get-ChildItem -Path $BackupDir -Filter "*_enc_backup_*.sql" |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1

        if ($null -eq $latestBackup) {
            Write-Log "No backup files found in $BackupDir"
            return $null
        }

        return $latestBackup.FullName
    } catch {
        Write-Log "Error finding latest backup: $_"
        return $null
    }
}

# Function to verify backup file decryption
function Test-BackupDecryption {
    param(
        [Parameter(Mandatory=$true)]
        [string]$BackupFile,
        
        [Parameter(Mandatory=$true)]
        [System.Security.SecureString]$Password
    )
    
    try {
        # Convert SecureString to plain text only within the local scope
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($Password)
        $plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
        
        # Test decryption
        $testResult = & $config.OpenSSLPath enc -d -aes-256-cbc -pbkdf2 -in $BackupFile -pass "pass:$plainPassword" -salt | Select-Object -First 1
        
        # Clear the plain text password
        $plainPassword = $null
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
        
        return $null -ne $testResult
    } catch {
        return $false
    } finally {
        # Ensure cleanup
        if ($plainPassword) { $plainPassword = $null }
        if ($BSTR) { [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR) }
    }
}

# Initialize environment
if (!(Initialize-RestoreEnvironment -Config $config)) {
    exit 1
}

# Parameter validation
if ([string]::IsNullOrWhiteSpace($config.DBUser) -or [string]::IsNullOrWhiteSpace($config.DBName)) {
    Write-Log "Database user or name cannot be empty"
    exit 1
}

# Find the latest backup file
$backupFile = Get-LatestBackup -BackupDir $config.BackupDir
if (!$backupFile) {
    Write-Log "No backup file found to restore"
    exit 1
}

Write-Log "Found backup file to restore: $backupFile"

# Prompt for MySQL password securely
$securePassword = Read-Host -Prompt "Enter MySQL password" -AsSecureString
$mysqlPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
)

# Prompt for backup decryption password securely
$secureDecPassword = Read-Host -Prompt "Enter the backup decryption password" -AsSecureString
$decPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureDecPassword)
)

# Verify decryption before attempting restore
if (!(Test-BackupDecryption -BackupFile $backupFile -Password $secureDecPassword)) {
    Write-Log "Failed to decrypt backup file. Please check the decryption password."
    exit 1
}

# Create a temporary file for the decrypted content
$tempFile = [System.IO.Path]::GetTempFileName()

try {
    Write-Log "Decrypting backup file..."
    
    # Decrypt the backup file
    & $config.OpenSSLPath enc -d -aes-256-cbc -pbkdf2 -in $backupFile -out $tempFile -pass "pass:$decPassword"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Decryption failed"
        exit 1
    }    Write-Log "Creating database if it doesn't exist..."
    # Create database if it doesn't exist
    $createDbCmd = "CREATE DATABASE IF NOT EXISTS $($config.DBName);"
    $createDbCmd | & $config.MySQLPath -u $config.DBUser "-p$mysqlPassword"

    Write-Log "Performing database restore..."
    # Perform the restore
    Get-Content $tempFile | & $config.MySQLPath -u $config.DBUser "-p$mysqlPassword" $config.DBName

    if ($LASTEXITCODE -eq 0) {
        Write-Log "Database restore completed successfully"
    } else {
        Write-Log "Database restore failed with exit code: $LASTEXITCODE"
        exit 1
    }
} catch {
    Write-Log "An error occurred during restore: $_"
    exit 1
} finally {
    # Clean up
    if (Test-Path $tempFile) {
        Remove-Item $tempFile -Force
        Write-Log "Cleaned up temporary files"
    }
}

# Clear sensitive data from memory
$mysqlPassword = $null
$securePassword = $null
$decPassword = $null
$secureDecPassword = $null
