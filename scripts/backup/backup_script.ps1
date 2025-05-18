<#
.SYNOPSIS
    MySQL Backup Script with Encryption
.DESCRIPTION
    This script performs a MySQL database backup, encrypts it using OpenSSL, and manages retention of backups.
.NOTES
    Original work from: https://github.com/kn-msccs-uol/collegedatabasesystem
    Originally licensed under MIT. Relicensed under BSD 3-Clause with permission
    from original author. Significant modifications made for uni-records-management-sys.
#>

# Configuration
$config = @{
    MySQLDumpPath = "C:\Program Files\MySQL\MySQL Server 9.3\bin\mysqldump.exe"
    OpenSSLPath = "C:\Program Files\Git\usr\bin\openssl.exe"
    DBUser = "root"
    DBName = "urms_dev"
    BackupDir = "C:\DBBackups\urms_dev"
    MaxVersions = 30
    TimeStampFormat = 'yyyyMMdd_HHmmss'
}

# Derived paths and values
$config.LogsDir = Join-Path $config.BackupDir "logs"
$timestamp = Get-Date -Format $config.TimeStampFormat
$logFile = Join-Path $config.LogsDir "backup_$timestamp.log"
$backupFile = Join-Path $config.BackupDir "$($config.DBName)_enc_backup_$timestamp.sql"

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
function Initialize-BackupEnvironment {
    param (
        [hashtable]$Config
    )
    
    # Validate required paths
    $requiredPaths = @{
        MySQLDump = $Config.MySQLDumpPath
        OpenSSL = $Config.OpenSSLPath
    }

    foreach ($path in $requiredPaths.GetEnumerator()) {
        if (!(Test-Path $path.Value)) {
            Write-Host "$($path.Key) not found at $($path.Value)"
            return $false
        }
    }

    # Create required directories if they don't exist
    try {
        if (!(Test-Path $Config.BackupDir)) {
            New-Item -ItemType Directory -Path $Config.BackupDir -ErrorAction Stop | Out-Null
            Write-Host "Created directory: $($Config.BackupDir)"
        }
        
        if (!(Test-Path $Config.LogsDir)) {
            New-Item -ItemType Directory -Path $Config.LogsDir -ErrorAction Stop | Out-Null
            Write-Host "Created directory: $($Config.LogsDir)"
        }
    } catch {
        Write-Host "Failed to create directory: $_"
        return $false
    }
    
    return $true
}

# Function to verify backup file decryption
function Test-BackupEncryption {
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

# Function to remove old files while keeping the specified number of latest versions
function Remove-OldFiles {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Path,
        
        [Parameter(Mandatory=$true)]
        [string]$Filter,
        
        [Parameter(Mandatory=$true)]
        [int]$MaxVersions
    )
    
    $files = Get-ChildItem -Path $Path -Filter $Filter | Sort-Object LastWriteTime -Descending
    if ($files.Count -gt $MaxVersions) {
        $filesToDelete = $files | Select-Object -Skip $MaxVersions
        foreach ($file in $filesToDelete) {
            try {
                Remove-Item $file.FullName -Force
                Write-Log "Removed old file: $($file.Name)"
            } catch {
                Write-Log "Failed to remove file $($file.Name): $_"
            }
        }
    }
}

# Initialize environment
if (!(Initialize-BackupEnvironment -Config $config)) {
    exit 1
}

# Parameter validation
if ([string]::IsNullOrWhiteSpace($config.DBUser) -or [string]::IsNullOrWhiteSpace($config.DBName)) {
    Write-Log "Database user or name cannot be empty"
    exit 1
}

# Generate timestamped backup file name
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = Join-Path $config.BackupDir "$($config.DBName)_enc_backup_$timestamp.sql"

# Prompt for MySQL password securely
$securePassword = Read-Host -Prompt "Enter MySQL password" -AsSecureString
$mysqlPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePassword)
)

# Prompt for backup encryption password securely
$secureEncPassword = Read-Host -Prompt "Enter the intended backup encryption password" -AsSecureString
$encPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureEncPassword)
)

# Build the mysqldump arguments
$arguments = @("-u", $config.DBUser, "-p$mysqlPassword", $config.DBName)

# Run mysqldump and capture errors
try {
    # Execute mysqldump and pipe directly to openssl with PBKDF2
    & $config.MySQLDumpPath @arguments | & $config.OpenSSLPath enc -aes-256-cbc -pbkdf2 -salt -out $backupFile -pass "pass:$encPassword"

    if ($LASTEXITCODE -eq 0) {
        # Verify backup file
        if (!(Test-Path $backupFile)) {
            Write-Log "Backup file was not created"
            exit 1
        }
        
        $fileSize = (Get-Item $backupFile).Length
        if ($fileSize -eq 0) {
            Write-Log "Backup file is empty"
            Remove-Item $backupFile
            exit 1
        }

        # Verify encryption
        if (!(Test-BackupEncryption -BackupFile $backupFile -Password $secureEncPassword)) {
            Write-Log "Backup encryption verification failed"
            Remove-Item $backupFile
            exit 1
        }

        Write-Log "Backup and encryption completed successfully: $backupFile"

        # Retention cleanup (keep only last 7 days of backups)
        try {
            Write-Log "Performing backup retention cleanup..."
            Remove-OldFiles -Path $config.LogsDir -Filter "*.log" -MaxVersions $config.MaxVersions
            Remove-OldFiles -Path $config.BackupDir -Filter "*.sql" -MaxVersions $config.MaxVersions
            
            $backupCount = (Get-ChildItem -Path $config.BackupDir -Filter "*.sql").Count
            $logCount = (Get-ChildItem -Path $config.LogsDir -Filter "*.log").Count
            Write-Log "Retention cleanup completed. Current counts - Backups: $backupCount, Logs: $logCount"
        } catch {
            Write-Log "Error during retention cleanup: $_"
        }
    } else {
        Write-Log "Backup process failed with exit code: $LASTEXITCODE"
    }
} catch {
    Write-Log "An error occurred during backup: $_"
}

# Clear sensitive data from memory
$mysqlPassword = $null
$securePassword = $null
$encPassword = $null
$secureEncPassword = $null
