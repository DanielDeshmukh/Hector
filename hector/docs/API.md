# HECTOR API Documentation

> REST API reference for HECTOR Legal Intelligence System

---

## Base URL

```
http://localhost:8000
```

## Authentication

### API Key Authentication
```bash
curl -H "X-API-Key: hector-dev-key" http://localhost:8000/status
```

### JWT Authentication
```bash
# Get token
curl -X POST "http://localhost:8000/auth/token?api_key=hector-dev-key"

# Use token
curl -H "Authorization: Bearer <token>" http://localhost:8000/status
```

---

## Endpoints

### GET /status

Health check and system status.

**Response:**
```json
{
  "status": "operational",
  "version": "2.1.0",
  "documents_indexed": 17832,
  "database_connected": true
}
```

---

### POST /search

Legal research search.

**Request:**
```json
{
  "query": "Section 302 BNS murder",
  "top_k": 10,
  "include_related": true,
  "format": "detailed"
}
```

**Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `query` | string | Search query (required) | - |
| `top_k` | int | Number of results | 10 |
| `include_related` | bool | Include related provisions | false |
| `format` | string | Output format: summary/detailed/citations | summary |
| `verify` | bool | Enable citation verification | false |

**Response:**
```json
{
  "results": [
    {
      "id": "doc_123",
      "content": "302. Whoever commits murder...",
      "source": "BNS 2023",
      "page": 45,
      "section": "302",
      "score": 0.95
    }
  ],
  "related_provisions": ["Section 303", "Section 304"],
  "verification_status": "verified"
}
```

---

### POST /compare

Compare IPC and BNS sections.

**Request:**
```json
{
  "ipc_section": "420",
  "bns_section": null
}
```

**Response:**
```json
{
  "ipc": {
    "section": "420",
    "title": "Cheating and dishonestly inducing delivery of property",
    "punishment": "Imprisonment up to 7 years + fine"
  },
  "bns": {
    "section": "318",
    "title": "Cheating and dishonestly inducing delivery of property",
    "punishment": "Imprisonment up to 7 years + fine"
  },
  "mapping_status": "direct_equivalent"
}
```

---

### POST /route

Classify user intent.

**Request:**
```json
{
  "query": "How to file for bail?"
}
```

**Response:**
```json
{
  "route": "LEGAL_RESEARCH",
  "hector_response": "Legal research signal detected.",
  "confidence": 0.93
}
```

---

### POST /ingest

Ingest a new document.

**Request:**
```json
{
  "file_path": "data/Books/new_act.pdf",
  "metadata": {
    "title": "New Legal Act",
    "year": 2024
  }
}
```

**Response:**
```json
{
  "status": "success",
  "documents_added": 50,
  "collection": "indian_law_bns"
}
```

---

### WebSocket /ws/search

Streaming search results.

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/search');

ws.send(JSON.stringify({
  query: "bail under CRPC",
  top_k: 5
}));

ws.onmessage = (event) => {
  console.log(JSON.parse(event.data));
};
```

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| /search | 60/minute |
| /compare | 60/minute |
| /route | 100/minute |
| /ingest | 10/hour |

---

## Error Responses

**400 Bad Request:**
```json
{
  "error": "Invalid query",
  "details": "Query too short"
}
```

**401 Unauthorized:**
```json
{
  "error": "Invalid API key"
}
```

**429 Too Many Requests:**
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 30
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error",
  "request_id": "abc123"
}
```

---

*See also: [CLI Reference](CLI_REFERENCE.md), [Search Syntax](SEARCH_SYNTAX.md)*