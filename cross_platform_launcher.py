import subprocess
import sys
import time
import webbrowser
from flask import Flask
import requests
from colorama import init, Fore, Back, Style, AnsiToWin32
import psutil
import signal
import os
import platform

# Initialize colorama with proper encoding
init(strip=False, convert=sys.platform.startswith('win'), autoreset=True)

# Force color support in non-TTY environments
os.environ['FORCE_COLOR'] = '1'

temp_files_to_cleanup = []

def get_system_powershell_path():
    """Check if PowerShell is already installed on the system and return its path."""
    system = platform.system()

    def pathfind_command(cmd):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split("\n")[0]  # Get first path
            return None
        except (subprocess.SubprocessError, FileNotFoundError):
            return None

    # Determine commands to check in priority order - PowerShell Core preferred
    commands = []
    if system == "Windows":
        commands.append(("where", "pwsh", "PowerShell Core"))
        commands.append(("where", "powershell.exe", "Windows PowerShell"))
    else:
        commands.append(("which", "pwsh", "PowerShell Core"))

    # Check each command in order of priority
    for cmd_name, executable, pwsh_type in commands:
        path = pathfind_command([cmd_name, executable])
        if path:
            print(f"\n{Fore.GREEN}✓ {pwsh_type} found on system: [\x1b[3m{Fore.MAGENTA}{path}{Style.RESET_ALL}{Fore.GREEN}].{Style.RESET_ALL}\nProceeding...\n")
            return path

    return None

def download_powershell_if_needed():
    """Download PowerShell Core only if not already available on the system."""
    # Check if PowerShell is already installed on the system
    system_path = get_system_powershell_path()
    if system_path:
        return system_path
    
    import zipfile
    import tarfile
    
    # Determine platform and architecture
    system = platform.system()
    architecture = "x64" if platform.machine().endswith('64') else "x86"
    
    # Set up download URLs and paths
    ps_dir = os.path.join(os.path.dirname(__file__), "bundled_powershell")
    os.makedirs(ps_dir, exist_ok=True)
    
    # Check if already downloaded
    bundled_path = os.path.join(ps_dir, "pwsh.exe" if system == "Windows" else "pwsh")
    if os.path.exists(bundled_path):
        print(f"\n{Fore.GREEN}✓ PowerShell Core (bundled) found on system: [\x1b[3m{Fore.MAGENTA}{bundled_path}{Style.RESET_ALL}{Fore.GREEN}].{Style.RESET_ALL}\nProceeding...\n")
        return bundled_path
    
    print(f"\n{Fore.YELLOW}### Hurdle (minor): no PowerShell installation found ###{Style.RESET_ALL}\n")
    
    # PowerShell Core download URLs (latest version)
    ps_urls = {
        "Windows": f"https://github.com/PowerShell/PowerShell/releases/download/v7.5.1/PowerShell-7.5.1-win-{architecture}.zip",
        "Darwin": f"https://github.com/PowerShell/PowerShell/releases/download/v7.5.1/powershell-7.5.1-osx-{architecture}.tar.gz",
        "Linux": f"https://github.com/PowerShell/PowerShell/releases/download/v7.5.1/powershell-7.5.1-linux-{architecture}.tar.gz"
    }
    
    if system in ps_urls:
        url = ps_urls[system]
        local_file = os.path.join(ps_dir, os.path.basename(url))
        
        # Download file
        print(f"Downloading PowerShell Core for {system}...")
        response = requests.get(url, stream=True)
        with open(local_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extract archive
        if local_file.endswith('.zip'):
            with zipfile.ZipFile(local_file, 'r') as zip_ref:
                zip_ref.extractall(ps_dir)
        else:
            with tarfile.open(local_file, 'r:gz') as tar_ref:
                tar_ref.extractall(ps_dir)
        
        # Make executable on Unix systems
        if system != "Windows":
            os.chmod(bundled_path, 0o755)
        
        # Cleanup download file
        os.remove(local_file)
        print(f"{Fore.GREEN}✓ PowerShell Core installed successfully{Style.RESET_ALL}")
        print(f"{Fore.GREEN}  ➥ now available on system at: [\x1b[3m{Fore.MAGENTA}{bundled_path}{Style.RESET_ALL}{Fore.GREEN}].{Style.RESET_ALL}\nProceeding...\n")
        
        return bundled_path
    
    print(f"\n{Fore.RED}✗ Unsupported system: {system}{Style.RESET_ALL}\n")
    return None

def get_powershell_path():
    """Get path to PowerShell executable (system or bundled)."""
    # Check for system PowerShell first
    system_path = get_system_powershell_path()
    if system_path:
        return system_path
    
    # Then check for/download bundled PowerShell
    return download_powershell_if_needed()

def run_powershell_script(script):
    """Run PowerShell script using available PowerShell."""
    # Get path to PowerShell executable
    pwsh_path = get_powershell_path()
    
    if not pwsh_path:
        print(f"{Fore.RED}✗ PowerShell is not available and could not be installed{Style.RESET_ALL}")
        return None, None, 1
    
    # Execute PowerShell script
    result = subprocess.run([
        pwsh_path, "-NoProfile", "-NonInteractive", "-Command", script
    ], capture_output=True, text=True)
    
    return result.stdout, result.stderr, result.returncode

def print_step(step_number, total_steps, message):
    """Print a formatted step message with progress indicator."""
    print(f"\n{Fore.CYAN}[Step {step_number}/{total_steps}] {message}{Style.RESET_ALL}\n")

def run_command(command, cwd=None):
    """Run a command and stream its output."""
    startupinfo = None
    if sys.platform.startswith('win'):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        cwd=cwd,
        encoding='utf-8',
        env={**os.environ, 'PYTHONIOENCODING': 'utf-8'},  # Force UTF-8 for Python subprocess
        startupinfo=startupinfo
    )

    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip(), flush=True)
            
    rc = process.poll()
    return rc

def start_flask_application():
    """Start the Flask application with RESTx and Swagger UI."""
    # Ensure no process is running on port 5000
    kill_process_on_port(5000)

    print("Waiting for Flask-RESTx (with Swagger UI) to start...")
    
    # Get virtual environment paths
    venv_path = os.path.join(os.getcwd(), ".venv", "Scripts" if sys.platform.startswith('win') else "bin")
    venv_python = os.path.join(venv_path, "python.exe" if sys.platform.startswith('win') else "python")
    if not os.path.exists(venv_python):
        print(f"{Fore.RED}✗ Virtual environment Python not found at {venv_python}{Style.RESET_ALL}\n")
        sys.exit(1)
    
    # Set environment variables for the new terminal
    powershell_env_setup = (
        "$env:VIRTUAL_ENV='" + os.path.dirname(venv_path).replace("'", "''") + "';",
        "$env:PATH='" + venv_path.replace("'", "''") + "' + [IO.Path]::PathSeparator + $env:PATH;"
        )
    
    # Launch Flask-RESTx debugger in a new terminal window
    try:
        # Get PowerShell path via detection
        pwsh_path = get_powershell_path()

        if pwsh_path:
            # PowerShell is available (either system or downloaded)
            powershell_cmd = (
                # Configure console for Unicode support
                '$OutputEncoding = [System.Text.Encoding]::UTF8;' +
                '[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;' +
                '[Console]::InputEncoding = [System.Text.Encoding]::UTF8;' +
                # Only use chcp on Windows
                ('' if not sys.platform.startswith('win') else 'chcp 65001 | Out-Null;') +
                f'Write-Host "===================================================================" -ForegroundColor Cyan;' +
                f'Write-Host "======= ~      Uni-Records-Management-Sys (URMS) APP      ~ =======" -ForegroundColor Cyan;' +
                f'Write-Host "===================================================================" -ForegroundColor Cyan;' +
                f'Write-Host "";' +
                f'Write-Host "Flask-RESTx (with Swagger UI)" -ForegroundColor Gray;' +
                f'Write-Host "";' +
                ''.join(powershell_env_setup) +
                f'cd "{os.getcwd()}";' +
                f'& "{venv_python}" run.py'
            )
            
            if sys.platform.startswith('win'):
                temp_script = os.path.join(os.environ.get('TEMP', os.getcwd()), 'urms_launch.ps1')
                with open(temp_script, 'w', encoding='utf-8') as f:
                    f.write(powershell_cmd)
                temp_files_to_cleanup.append(temp_script)

                cmd = f'start "" "{pwsh_path}" -NoLogo -NoExit -NoProfile -ExecutionPolicy Bypass -File "{temp_script}"'

                subprocess.Popen(cmd, shell=True)

            elif sys.platform == "darwin":  # macOS
                temp_script = os.path.join(os.path.expanduser("~/Library/Caches"), 'urms_launch.ps1')
                with open(temp_script, 'w', encoding='utf-8') as f:
                    f.write(powershell_cmd)
                temp_files_to_cleanup.append(temp_script)

                # Make it executable
                os.chmod(temp_script, 0o755)

                # Use AppleScript to open Terminal with PowerShell executing the script
                apple_script = (
                    f'tell application "Terminal" to do script '
                    f'"{pwsh_path} -NoLogo -NoExit -NoProfile -File \\"{temp_script}\\""'
                    )
                
                subprocess.Popen(['osascript', '-e', apple_script])

            else:  # Linux
                temp_script = os.path.join("/tmp", 'urms_launch.ps1')
                with open(temp_script, 'w', encoding='utf-8') as f:
                    f.write(powershell_cmd)
                temp_files_to_cleanup.append(temp_script)
                
                # Make it executable
                os.chmod(temp_script, 0o755)

                # Create a shell wrapper script that launches PowerShell with our script
                wrapper_script = os.path.join("/tmp", 'urms_launch.sh')
                with open(wrapper_script, 'w', encoding='utf-8') as f:
                    f.write(f'#!/bin/bash\n{pwsh_path} -NoLogo -NoExit -NoProfile -File "{temp_script}"\n')
                temp_files_to_cleanup.append(wrapper_script)

                # Make it executable
                os.chmod(wrapper_script, 0o755)

                # Find a suitable terminal emulator
                terminals = ["gnome-terminal", "konsole", "xterm", "xfce4-terminal", "terminator"]
                terminal_cmd = next((t for t in terminals if subprocess.run(["which", t], capture_output=True).returncode == 0), "xterm")
                
                # Different terminals have different command line syntax
                if terminal_cmd == "gnome-terminal":
                    subprocess.Popen([terminal_cmd, "--", wrapper_script])
                else:
                    subprocess.Popen([terminal_cmd, '-e', wrapper_script])
            
            print(f"{Fore.GREEN}✓ Launched Standalone Debug Terminal using PowerShell{Style.RESET_ALL}\n")
        else:
            # Fallback to system default terminal if PowerShell is not available (untested)
            print(f"{Fore.YELLOW}PowerShell not available, using system terminal (untested)...{Style.RESET_ALL}\n")
            if sys.platform.startswith('win'):
                subprocess.Popen(['start', 'cmd', '/k', f'cd /d {os.getcwd()} && {venv_python} run.py'], shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(['open', '-a', 'Terminal', f'cd {os.getcwd()} && python run.py'])
            else:  # Linux
                #Find a suitable terminal emulator
                terminals = ["gnome-terminal", "konsole", "xterm", "xfce4-terminal", "terminator"]
                terminal_cmd = next((t for t in terminals if subprocess.run(["which", t], capture_output=True).returncode == 0), "xterm")
                
                subprocess.Popen([terminal_cmd, '--', 'python', 'run.py'])
                print(f"{Fore.RED}✗ No suitable terminal emulator found. Please run the Flask app manually.{Style.RESET_ALL}\n")
                sys.exit(1)

    except Exception as e:
        print(f"{Fore.RED}✗ Failed to launch Standalone Debug Terminal: {str(e)}{Style.RESET_ALL}\n")
        sys.exit(1)
    
    # Wait for Flask to be ready
    if not wait_for_flask():
        print(f"{Fore.RED}✗ Flask server failed to start{Style.RESET_ALL}\n")
        sys.exit(1)

def wait_for_flask(url="http://localhost:5000/", max_attempts=30):
    """Wait for Flask server and Swagger UI to be ready."""
    print("...check external window...")
    attempt = 0
    while attempt < max_attempts:
        try:
            response = requests.get(url)
            if response.status_code in [200, 404]:
                print(f"{Fore.GREEN}✓ Flask-RESTx (with Swagger UI) is ready!{Style.RESET_ALL}")
                return True
        except requests.exceptions.ConnectionError:
            pass
        
        time.sleep(1)
        attempt += 1
        sys.stdout.write('.')
        sys.stdout.flush()
    
    return False

def kill_process_on_port(port):
    """Kill any process running on the specified port."""
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            for conn in proc.net_connections():
                if conn.laddr.port == port:
                    os.kill(proc.pid, signal.SIGTERM)
                    time.sleep(1)  # Give it time to shutdown gracefully
                    return
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def check_migrations_folder_nonempty():
    """Check if the migrations folder exists and is not empty."""
    migrations_folder = os.path.join(os.getcwd(), "migrations")
    if not os.path.isdir(migrations_folder):
        return False

    has_files = False
    has_versions_dir = False

    for entry in os.scandir(migrations_folder):
        if entry.is_file():
            has_files = True
        elif entry.is_dir() and entry.name == "versions":
            has_versions_dir = True

    return has_files and has_versions_dir

def open_web_browser():
    """Open the API documentation in a web browser."""
    webbrowser.open('http://localhost:5000/api/docs')

def cleanup_temp_files():
    if not temp_files_to_cleanup:
        print(f"\n{Fore.GREEN}✓ No temporary files to cleanup{Style.RESET_ALL}\n")
        return
    
    print(f"\n* Wrapping up: cleaning up temporary files...")
    success_count = 0

    for file_path in temp_files_to_cleanup:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"  - {file_path}")
                success_count += 1
            else:
                # File doesn't exist, so we consider it already cleaned up
                success_count += 1
        except Exception as e:
            print(f"{Fore.RED}✗ - {file_path}: {e}{Style.RESET_ALL}")

    if success_count == len(temp_files_to_cleanup):
        print(f"{Fore.GREEN}✓ Cleanup complete{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.YELLOW}⚠ Partial cleanup completed ({success_count}\n leftover files:{len(temp_files_to_cleanup)} files){Style.RESET_ALL}\n")

def show_completion_message():
    """Show the final completion message to the user."""
    print(f"\n{Fore.CYAN}The Flask server is running in a separate terminal window.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}You can close that window when you're done with the application.{Style.RESET_ALL}")

def main():
    print(
        f"\n{Fore.BLACK}{Back.WHITE}WELCOME TO "
        f"{Fore.BLUE}Uni-Records-Management-Sys"
        f"{Fore.BLACK} (URMS)!{Style.RESET_ALL}\n"
        f"\n"
        f"\n{Fore.CYAN}----- Launcher -----{Style.RESET_ALL}\n"
        f"\n"
        f"{Fore.YELLOW}Select Option:\n"
        f"{Fore.CYAN}  1. Setup\n"
        f"{Fore.CYAN}  2. Application\n"
        f"{Fore.CYAN}{Style.DIM}  0. Exit Launcher{Style.RESET_ALL}\n"
        f"\n{Fore.CYAN}--------------------{Style.RESET_ALL}\n"
    )

    while True:
        choice = input(f"{Fore.GREEN}Enter your choice (1, 2, or 0): {Style.RESET_ALL}").strip()

        if choice not in ['1', '2', '0']:
            print(f"{Fore.RED}✗ Invalid choice. Please enter 1, 2, or 0.{Style.RESET_ALL}")
        elif choice == '0':
            print(f"\n{Fore.MAGENTA}{Style.BRIGHT}Exiting Launcher. Goodbye!{Style.RESET_ALL}")
            sys.exit(0)
        elif choice == '2':
            print(f"\n{Fore.CYAN}========== Uni-Records-Management-Sys APP =========={Style.RESET_ALL}\n")

            start_flask_application()
            time.sleep(1)
            open_web_browser()

            cleanup_temp_files()
            show_completion_message()
            sys.exit(0)
        else:
            print(f"\n{Fore.CYAN}========== Uni-Records-Management-Sys SETUP =========={Style.RESET_ALL}\n")

            total_steps = 5
            current_step = 1

            print_step(current_step, total_steps, "Starting Flask application with RESTx and Swagger UI")

            start_flask_application() # Step 1

            current_step += 1
        
            # Step 2: Initialize Flask-Migrate
            print_step(current_step, total_steps, "Initializing Flask-Migrate")
            if run_command("flask db init") != 0:
                print(f"{Fore.RED}✗ Flask-Migrate initialization failed{Style.RESET_ALL}")
                sys.exit(1)
            print(f"{Fore.GREEN}✓ Flask-Migrate initialized successfully (you can ignore the alembic.ini message){Style.RESET_ALL}")
            time.sleep(2)
            
            current_step += 1

            # Step 3: Create initial migration
            print_step(current_step, total_steps, "Creating initial database migration")
            if run_command('flask db migrate -m "Initial migration."') != 0:
                print(f"{Fore.RED}✗ Database migration failed{Style.RESET_ALL}")
                sys.exit(1)
            
            # Verify migration creation
            if check_migrations_folder_nonempty():
                print(f"{Fore.GREEN}✓ Database migration created successfully{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Migration folder was not created{Style.RESET_ALL}")
                sys.exit(1)
            time.sleep(2)

            current_step += 1

            # Step 4: Seed the database
            print_step(current_step, total_steps, "Seeding the database with sample data (expanded)")
            if run_command("python -m scripts.seed_database_expanded") != 0:
                print(f"{Fore.RED}✗ Database seeding failed{Style.RESET_ALL}")
                sys.exit(1)
            print(f"{Fore.GREEN}✓ Database seeded successfully{Style.RESET_ALL}")
            time.sleep(2)

            current_step += 1

            # Step 5: Open API documentation
            print_step(current_step, total_steps, "Opening API documentation in web browser")
            
            open_web_browser()
            
            print(f"\n{Fore.GREEN}✓ ALL SETUP STEPS COMPLETED SUCCESSFULLY! ✓{Style.RESET_ALL}")

            cleanup_temp_files()
            show_completion_message()
            sys.exit(0)

if __name__ == "__main__":
    main()
