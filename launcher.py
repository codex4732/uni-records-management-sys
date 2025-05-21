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

# Initialize colorama with proper encoding
init()
sys.stdout = AnsiToWin32(sys.stdout, convert=True, strip=False, autoreset=True)

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
    if sys.platform.startswith('win'):
        venv_path = os.path.join(os.getcwd(), ".venv", "Scripts")
        venv_python = os.path.join(venv_path, "python.exe")
    else:
        venv_path = os.path.join(os.getcwd(), ".venv", "bin")
        venv_python = os.path.join(venv_path, "python")
    if not os.path.exists(venv_python):
        print(f"{Fore.RED}✗ Virtual environment Python not found at {venv_python}{Style.RESET_ALL}\n")
        sys.exit(1)

    # Set environment variables for the new terminal
    powershell_env_setup = (
        "$env:VIRTUAL_ENV='" + os.path.dirname(venv_path) + "';",
        "$env:PATH='" + venv_path + ";" + os.environ['PATH'] + "';"
    )

    # Launch Flask-RESTx debugger in a new terminal window
    try:
        if sys.platform.startswith('win'):
            powershell_cmd = (
                # Configure console for Unicode support
                '$OutputEncoding = [System.Text.Encoding]::UTF8;' +
                '[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;' +
                '[Console]::InputEncoding = [System.Text.Encoding]::UTF8;' +
                'chcp 65001 | Out-Null;' +
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

            subprocess.Popen(
                ['start', 'powershell.exe', '-NoExit', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', powershell_cmd],
                shell=True
            )
            print(f"{Fore.GREEN}✓ Launched Standalone Debug Terminal{Style.RESET_ALL}\n")
        else:
            # On macOS, use AppleScript to open Terminal and run the Flask app
            cwd = os.getcwd().replace('"', '\\"')
            python_exec = venv_python.replace('"', '\\"')
            run_script = os.path.join(cwd, 'run.py').replace('"', '\\"')
            apple_script = (
                f'tell application "Terminal" to do script '
                f'"cd \\"{cwd}\\" && \\"{python_exec}\\" \\"{run_script}\\""\n'
            )
            subprocess.Popen(['osascript', '-e', apple_script])
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

            print(f"\n{Fore.CYAN}The Flask server is running in a separate terminal window.{Style.RESET_ALL}")
            print(f"{Fore.CYAN}You can close that window when you're done with the application.{Style.RESET_ALL}")
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
            print(f"\n{Fore.CYAN}The Flask server is running in a separate terminal window.{Style.RESET_ALL}")
            print(f"{Fore.CYAN}You can close that window when you're done with the application.{Style.RESET_ALL}")
            sys.exit(0)

if __name__ == "__main__":
    main()
