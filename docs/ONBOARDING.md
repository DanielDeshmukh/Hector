# HECTOR Legal Researcher Onboarding Guide

> A comprehensive guide for legal professionals using HECTOR

---

## Welcome to HECTOR

HECTOR (Hierarchical Evaluation of Civil-Criminal Textual's Orchestrator & Retrieval) is an AI-powered legal research assistant designed specifically for Indian law. It helps you:

- Find relevant legal provisions instantly
- Compare IPC with BNS (new criminal law)
- Get accurate citations from authoritative sources
- Research case law efficiently

---

## Getting Started

### 1. Understanding the Interface

**Main Search Bar**: Enter your legal queries here
- Supports natural language
- Recognizes legal terms and section numbers

**Dual-Pane Viewer**:
- Left: AI-generated summary
- Right: Source document

**Format Selector**: Switch between Summary, Detailed, and Citations views

### 2. Basic Search

Try these first queries:

```
1. What is Section 302 BNS?
2. How to file for bail?
3. IPC 420 punishment
```

### 3. Understanding Results

HECTOR provides:
- **Relevant sections** from Bare Acts
- **Citations** with source and page numbers
- **Related provisions** for broader context
- **Verification status** showing citation accuracy

---

## Key Features

### 1. IPC to BNS Mapping

HECTOR automatically maps old IPC sections to new BNS:

| Old (IPC) | New (BNS) |
|-----------|-----------|
| Section 302 | Section 302 |
| Section 420 | Section 318 |
| Section 376 | Section 64 |

**Try**: "Compare IPC 420 with BNS equivalent"

### 2. Citation Verification

HECTOR verifies every citation:
- Checks section number validity
- Confirms act name (BNS/IPC/CRPC)
- Validates source references

### 3. Related Provisions

When you search for a section, HECTOR automatically shows:
- Related sections in same chapter
- Similar offenses
- Procedural requirements

---

## Common Use Cases

### For Criminal Lawyers

**Bail Applications**
```
Search: "anticipatory bail Section 438 CRPC"
View: Detailed format
Check: Related provisions for strong grounds
```

**Trial Preparation**
```
Search: "Section 302 evidence required"
View: Citations only
Check: Case precedents in results
```

### For Civil Lawyers

**Civil Procedure**
```
Search: "Order 39 Rule 1 CPC injunction"
View: Detailed format
Check: Recent amendments
```

**Property Disputes**
```
Search: "partition suit CPC"
View: Summary
Check: Limitation period
```

### For Law Students

**Exam Preparation**
```
Search: "elements of murder"
View: Summary
Use: Related provisions for comprehensive notes
```

**Case Analysis**
```
Search: "dying declaration evidence"
View: Detailed
Check: Judicial precedents
```

---

## Search Strategies

### 1. Be Specific
```
Good: "Section 302 BNS punishment"
Avoid: "murder law"
```

### 2. Include Context
```
Good: "bail under Section 437 CRPC conditions"
Avoid: "bail conditions"
```

### 3. Use Legal Terminology
- Use "cognizable offense" not "serious crime"
- Use "bailable" not "can get bail"
- Use "compoundable" not "can be settled"

### 4. Check Both Old and New Law
```
Search: "IPC 420"
Then: "BNS equivalent"
```

---

## Best Practices

### 1. Verify Citations
Always cross-check with original Bare Acts. HECTOR provides verification status - green means verified.

### 2. Use Related Provisions
Don't just read the main section - explore related provisions for complete understanding.

### 3. Check Effective Dates
- IPC: Pre-July 2024
- BNS: Post-July 2024
- BNSS: Post-July 2024

### 4. Keep Updated
HECTOR's Gazette scraper monitors amendments. Check for new updates regularly.

---

## Troubleshooting

### "No results found"
- Try different keywords
- Check spelling
- Use broader terms

### "Unexpected results"
- Add more context
- Specify the act (BNS/IPC)
- Use quotes for phrases

### "Citation not verified"
- The section may be new
- Check official Bare Acts
- Use Detailed format

---

## Advanced Features

### 1. API Access
For automated workflows, use HECTOR's REST API:
```bash
POST /search
{
  "query": "Section 302 BNS",
  "verify": true
}
```

### 2. CLI Commands
```bash
hector init          # Start application
hector status        # Check system
hector ingest        # Add new books
```

### 3. Offline Mode
For remote work, use offline bundles:
```python
from core.offline import OfflineMode
mode.enable_offline_mode("bundles/legal-v1")
```

---

## Security & Compliance

### Data Privacy
- Your searches are logged for improvement
- No personal data stored
- API keys are encrypted

### Citation Standards
- All citations verified
- Sources from official Bare Acts
- Page numbers accurate

---

## Support

### Documentation
- [Quick Start Guide](QUICKSTART.md)
- [CLI Reference](CLI_REFERENCE.md)
- [API Documentation](API.md)
- [Search Syntax](SEARCH_SYNTAX.md)

### Getting Help
- Check [Examples](EXAMPLES.md) for query patterns
- Review [Search Syntax](SEARCH_SYNTAX.md) for operators
- Use CLI `--help` for commands

---

## What's Next?

1. **Explore**: Try different search patterns
2. **Learn**: Read the search syntax guide
3. **Automate**: Use API for bulk research
4. **Stay Updated**: Enable Gazette monitoring

---

*Welcome to efficient legal research with HECTOR!*

For questions, refer to documentation or contact support.