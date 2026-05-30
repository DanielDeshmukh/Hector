# HECTOR CLI Setup

## Quick Start

Run HECTOR using the `hector` command from the project directory:

```bash
cd "d:\Vs Code\VS code\Hector"

# Show help
./hector --help
./hector

# Start HECTOR (API + Frontend)
./hector init

# Start HECTOR (API only)
./hector init --no-frontend

# Custom API port
./hector init --port 9000

# Auto-detect available ports
./hector init --auto-port

# Kill existing processes and start
./hector init --kill-existing

# Ingest books
./hector ingest

# Check system status
./hector status
```

## Global Access (Optional)

To use `hector` command from anywhere:

### Option 1: Add to PATH (Windows PowerShell - Admin)
```powershell
$projectPath = "d:\Vs Code\VS code\Hector"
[Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";$projectPath", "User")
```

### Option 2: Create Symlink (Windows PowerShell - Admin)
```powershell
New-Item -ItemType SymbolicLink -Path "$PROFILE\..\hector" -Target "d:\Vs Code\VS code\Hector\hector"
```

### Option 3: Git Bash Alias
Add to your `~/.bashrc`:
```bash
alias hector='cd "d:/Vs Code/VS code/Hector" && ./hector'
```

## Process Management

When you press **Ctrl+C** during `hector init`:
- All services are terminated gracefully
- Any stuck processes on the ports are automatically cleaned up
- Ports are released for reuse

## Troubleshooting

### Port Already in Use
```bash
# Use auto-port detection
./hector init --auto-port

# Or use custom port
./hector init --port 8001
```

### Stuck Processes
The cleanup is automatic on Ctrl+C. If processes are still stuck:
```bash
# Force kill existing processes on default ports
./hector init --kill-existing

# Or specify different ports
./hector init --port 9000 --frontend-port 3001
```

## Environment

The `hector` script automatically:
1. Activates the Python virtual environment (`venv`)
2. Runs the appropriate command
3. Cleans up processes on exit

**No need to manually activate the venv!** ✅
