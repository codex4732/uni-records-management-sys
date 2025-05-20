<#
.SYNOPSIS
    MySQL Backup Decryption Script
.DESCRIPTION
    This script decrypts MySQL database backups that were encrypted using OpenSSL AES-256-CBC.
    It can either work with the most recent encrypted backup or a specified file.
.NOTES
    Original work from: https://github.com/kn-msccs-uol/collegedatabasesystem
    Originally licensed under MIT. Relicensed under BSD 3-Clause with permission
    from original author. Significant modifications made for uni-records-management-sys.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$InputFile,
    
    [Parameter(Mandatory=$false)]
    [string]$OutputPath,
    
    [Parameter(Mandatory=$false)]
    [securestring]$DecryptionPassword
)

# Configuration
$config = @{
    OpenSSLPath = "C:\Program Files\Git\usr\bin\openssl.exe"
    BackupDir = "C:\DBBackups\urms_dev"
    TimeStampFormat = 'yyyyMMdd_HHmmss'
    ValidExtensions = @('.sql')
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
            Write-Log "No encrypted backup files found in $BackupDir"
            return $null
        }

        return $latestBackup.FullName
    } catch {
        Write-Log "Error finding latest encrypted backup: $_"
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

# Function to verify file validity
function Test-BackupFile {
    param(
        [Parameter(Mandatory=$true)]
        [string]$FilePath
    )
    
    if (!(Test-Path $FilePath)) {
        Write-Log "File not found: $FilePath"
        return $false
    }
    
    $extension = [System.IO.Path]::GetExtension($FilePath)
    if ($extension -notin $config.ValidExtensions) {
        Write-Log "Invalid file extension: $extension. Must be one of: $($config.ValidExtensions -join ', ')"
        return $false
    }
    
    return $true
}

# Initialize environment
if (!(Initialize-RestoreEnvironment -Config $config)) {
    exit 1
}

# Handle input file parameter
if ($InputFile) {
    if (!(Test-BackupFile -FilePath $InputFile)) {
        exit 1
    }
    $backupFile = $InputFile
} else {
    # Find the latest backup file
    $backupFile = Get-LatestBackup -BackupDir $config.BackupDir
    if (!$backupFile) {
        Write-Log "No backup file found to decrypt"
        exit 1
    }
}

Write-Log "Using backup file: $backupFile"

# Handle password parameter or prompt
if (!$DecryptionPassword) {
    $secureDecPassword = Read-Host -Prompt "Enter the backup decryption password" -AsSecureString
} else {
    $secureDecPassword = $DecryptionPassword
}

# Verify decryption before attempting to save
if (!(Test-BackupDecryption -BackupFile $backupFile -Password $secureDecPassword)) {
    Write-Log "Failed to decrypt backup file. Please check the decryption password."
    exit 1
}

# Handle output path
if ($OutputPath) {
    $outputDir = Split-Path $OutputPath
    if (!(Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    }
    $decryptedFile = $OutputPath
} else {
    # Preserve original filename while adding _decrypt suffix
    $directory = [System.IO.Path]::GetDirectoryName($backupFile)
    $filename = [System.IO.Path]::GetFileNameWithoutExtension($backupFile)
    $extension = [System.IO.Path]::GetExtension($backupFile)
    $decryptedFile = Join-Path $directory "$filename`_decrypt$extension"
}

try {
    Write-Log "Decrypting backup file..."
    
    # Check source file size and available space
    $sourceFile = Get-Item $backupFile
    $targetDrive = Split-Path $decryptedFile -Qualifier
    $freeSpace = (Get-PSDrive $targetDrive.TrimEnd(':')).Free
    
    if ($sourceFile.Length -gt $freeSpace) {
        Write-Log "Not enough space on target drive. Required: $($sourceFile.Length), Available: $freeSpace"
        exit 1
    }
    
    # Verify output path is writable
    try {
        [System.IO.File]::OpenWrite($decryptedFile).Close()
    } catch {
        Write-Log "Cannot write to output location: $decryptedFile"
        exit 1
    }
    
    # Convert SecureString to plain text for OpenSSL
    $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureDecPassword)
    $decPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    
    # Decrypt the backup file
    $result = & $config.OpenSSLPath enc -d -aes-256-cbc -pbkdf2 -in $backupFile -out $decryptedFile -pass "pass:$decPassword" 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Decryption failed: $result"
        exit 1
    }

    Write-Log "File successfully decrypted and saved as: $decryptedFile"
} catch {
    Write-Log "An error occurred during decryption: $_"
    exit 1
} finally {
    # Clear sensitive data from memory
    if ($BSTR) { [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR) }
    $decPassword = $null
    $secureDecPassword = $null
}
