# HECTOR CLI Reference

> Complete command-line interface documentation

---

## Commands

### hector init

Start HECTOR application (API server + Frontend).

```bash
hector init [OPTIONS]
```

**Options:**
| Flag | Description | Default |
|------|-------------|---------|
| `-p, --port` | API server port | 8000 |
| `-fp, --frontend-port` | Frontend dev server port | 3000 |
| `--no-frontend` | Start API only (no frontend) | false |

**Examples:**
```bash
hector init                    # Start both API and frontend
hector init --port 9000       # Custom API port
hector init --no-frontend     # API server only
```

---

### hector status

Display system status and statistics.

```bash
hector status
```

**Output includes:**
- Database connection status
- Total indexed documents
- Available books in data/Books
- Environment status (installed packages)

---

### hector ingest

Ingest legal documents from `data/Books` directory.

```bash
hector ingest [OPTIONS]
```

**Options:**
| Flag | Description | Default |
|------|-------------|---------|
| `-f, --force` | Re-ingest all books | false |
| `-v, --verbose` | Show detailed progress | false |

**Examples:**
```bash
hector ingest                  # Ingest new books only
hector ingest --force         # Re-ingest all books
```

---

### hector --help

Display help message.

```bash
hector --help
hector help
```

---

## Interactive Mode

Run without commands to start interactive CLI:

```bash
hector
```

This launches the Rich-based interactive terminal with:
- Auto-complete suggestions
- Route diagnostics
- Color-coded output

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API for LLM routing | Required |
| `HF_HUB_DISABLE_SYMLINKS_WARNING` | Suppress warnings | 1 |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (missing deps, invalid command) |
| 130 | Interrupted (Ctrl+C) |

---

*See also: [Quick Start Guide](QUICKSTART.md), [API Documentation](API.md)*