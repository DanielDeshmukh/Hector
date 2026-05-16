# HECTOR Quick Start Guide

> Get up and running with HECTOR Legal Intelligence System in 5 minutes

---

## Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend)
- 4GB RAM minimum
- 10GB disk space

## Installation

### 1. Clone and Setup

```bash
# Clone repository
git clone <hector-repo>
cd Hector

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Start HECTOR

```powershell
# Using CLI (recommended)
hector init

# Or manually
uvicorn api.app:app --reload
```

### 3. Access the UI

Open browser: http://localhost:3000

---

## First Search

Try these example queries:

```
What is Section 302 BNS?
Compare IPC 420 with BNS equivalent
How to file for anticipatory bail?
```

---

## Common Commands

| Task | Command |
|------|---------|
| Start application | `hector init` |
| Check status | `hector status` |
| Ingest books | `hector ingest` |
| View help | `hector --help` |

---

## Troubleshooting

**Q: Commands not found**
```powershell
# Add to PATH
[Environment]::SetEnvironmentVariable("Path", [System.Environment]::GetEnvironmentVariable("Path", "User") + ";D:\Vs Code\VS code\Hector", "User")
```

**Q: Database errors**
```bash
# Re-ingest documents
hector ingest --force
```

---

*Next: See [CLI Reference](CLI_REFERENCE.md) or [API Documentation](API.md)*