# HECTOR Search Syntax Guide

> Advanced search operators and techniques for legal research

---

## Basic Search

### Simple Queries
```
murder                              # Search for murder
theft section                       # Search for theft and sections
bail application                     # Search for bail applications
```

### Case Insensitive
All searches are case-insensitive:
```
Section 302
section 302
SECTION 302
```

---

## Legal Act References

### Section Numbers
```
Section 302            # BNS Section (default)
Section 302 IPC        # Specific to IPC
Section 302 BNS        # Specific to BNS
302 BNS                # Without "Section" keyword
```

### Multiple Sections
```
Section 302, 303, 304  # Multiple sections
Order 1 Rule 1 CPC    # CPC sections
```

---

## Act Names

| Code | Full Name |
|------|-----------|
| BNS | Bharatiya Nyaya Sanhita |
| BNSS | Bharatiya Nagarik Suraksha Sanhita |
| BSA | Bharatiya Sakshya Adhiniyam |
| IPC | Indian Penal Code |
| CRPC | Code of Criminal Procedure |
| CPC | Code of Civil Procedure |
| IEA | Indian Evidence Act |

**Examples:**
```
BNS Section 302
IPC 420 cheating
CRPC bail application
CPC Order 39 Rule 1
```

---

## Search Operators

### AND (Default)
```
murder theft           # Both terms must appear
Section 302 IPC murder # All terms must appear
```

### OR
```
murder | theft         # Either term
Section 302 | 303      # Either section
```

### NOT
```
murder -theft          # murder but not theft
bail -anticipatory     # bail but not anticipatory
```

---

## Phrase Search

Use quotes for exact phrases:
```
"cruelty of wife"
"death in police custody"
"without reasonable doubt"
```

---

## Wildcards

### Partial Matching
```
murde*                 # murder, murdering, murdered
thef*                 # theft, thefts, thief
bail*                 # bail, bailable, bailment
```

---

## Legal Keywords

### Offense Types
```
murder                # Intentional killing
manslaughter         # Unintentional killing
theft                # Dishonest taking
robbery              # Theft with violence
extortion             # Obtaining by threat
cheating              # Fraudulent deception
rape                  # Sexual assault
kidnapping           # Wrongful confinement
```

### Legal Procedures
```
FIR                   # First Information Report
bail                  # Release on bail
anticipatory bail     # Pre-arrest bail
arrant                # Judicial custody
summons               # Court summons
warrant               # Arrest warrant
charge sheet          # Prosecution document
```

### Punishment Keywords
```
imprisonment          # Jail term
fine                  # Monetary penalty
death penalty         # Capital punishment
rigorous imprisonment # Hard labor
simple imprisonment   # Basic jail
```

---

## Filters

### Act Filter
```
[IPC] murder
[BNS] theft
[CPC] partition
```

### Section Filter
```
section:302
order:1 rule:1
```

### Year Filter (for case law)
```
(2023) murder
(2020-2023) Supreme Court
```

---

## Advanced Examples

### Criminal Law
```
BNS Section 302 murder punishment
IPC 420 cheating imprisonment
bail under Section 437 CRPC
first information report FIR
```

### Civil Law
```
CPC Order 39 Rule 1 injunction
civil suit partition property
maintenance under Hindu Marriage Act
```

### Evidence
```
confession to police inadmissible
dying declaration evidence
expert testimony Indian Evidence Act
```

### Constitutional
```
fundamental rights Article 21
writ petition Supreme Court
basic structure doctrine
```

---

## Search Tips

1. **Start Broad**: Begin with general terms, then narrow down
2. **Use Act Codes**: Specify BNS/IPC/CPC for accuracy
3. **Add Context**: Include related terms like "punishment" or "procedure"
4. **Check Variations**: Try both IPC and BNS for older/newer laws

---

## Response Formats

### Summary (default)
Concise answer with key points and primary citation.

### Detailed
Full analysis with:
- Section text
- Chapter context
- Related provisions
- Case citations

### Citations Only
List of relevant sections with citations, no analysis.

---

*See also: [Example Queries](EXAMPLES.md), [CLI Reference](CLI_REFERENCE.md)*