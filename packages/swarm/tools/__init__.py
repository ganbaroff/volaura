"""Swarm Tools — give agents REAL capabilities, not just opinions.

Each tool is a Python function that an agent perspective can invoke
during autonomous_run.py execution. Tools are the difference between
"here's what I'd fix" and "here's the fix."

Tool categories:
- code: read files, search codebase, check for patterns
- db: query Supabase schema, check RLS, count rows
- deploy: check Vercel/Railway status, read logs
- test: run TypeScript check, lint, specific test suites
- constitution: verify code against Constitution rules
"""
