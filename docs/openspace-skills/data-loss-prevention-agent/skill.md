# Data Loss Prevention Agent Skill

## Metadata
- name: data-loss-prevention-agent
- description: Detect and prevent potential data leaks, ensuring the security and privacy of user data
- tags: security, data loss prevention, volaura

## Skill

When reviewing a new FastAPI endpoint for Volaura, check for potential data leaks:

1. **Sensitive Data** — No passwords, tokens, or PII in log output or error messages.
2. **Data Encryption** — All sensitive data is encrypted in transit and at rest.
3. **Access Control** — Only authorized users can access sensitive data.
4. **Audit Logging** — All data access and modifications are logged and monitored.

Severity: P0 = data leak, P1 = unauthorized access, P2 = logging gap, P3 = encryption weakness.
