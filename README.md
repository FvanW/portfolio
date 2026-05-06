# Frederick Van Wagenen — Technical Portfolio

> Army NCO | Systems Automation Engineer | Building toward ETS 2030

**Contact:** fvanwagenen@gmail.com | [LinkedIn](https://linkedin.com/in/frederickvanwagenen) | San Antonio, TX

---

## About

I'm an Army Staff Sergeant with a background in operations and training, currently building production-grade automation and infrastructure systems to transition into a technical career by 2030. Everything here is self-hosted, self-built, and battle-tested on real daily workflows.

This portfolio documents systems I've designed, implemented, and run 24/7 on my own hardware.

---

## Core Competencies

| Domain | Skills |
|--------|--------|
| **Automation & Orchestration** | Python, cron scheduling, multi-agent AI systems, event-driven workflows |
| **Cloud & Infrastructure** | Ubuntu Server 24.04, Docker, GitHub Actions, SSH hardening, reverse proxy |
| **AI/ML Integration** | LLM API orchestration (Kimi, Gemini, Claude), MCP protocol, prompt engineering, local inference (Ollama) |
| **Data Engineering** | ETL pipelines, API integration (Gmail, Notion, Google Drive, Telegram), structured output (JSON/regex) |
| **DevOps Practices** | Git workflows, CI/CD basics, configuration management, log aggregation, cost monitoring |
| **Security** | OAuth token management, credential isolation, least-privilege API access, network segmentation |

---

## Featured Projects

### [Hermes Agent — Personal AI Orchestration Platform](projects/hermes-agent/)

A multi-model, multi-tool AI agent system running 24/7 on a self-hosted Ubuntu server. Handles email triage, financial tracking, research compilation, smart home control, and daily digests — all without paid automation platforms like n8n or Zapier.

**Key achievements:**
- 11 automated cron jobs running daily, processing 100+ emails/day
- Multi-provider LLM fallback chain (Kimi → Gemini → Claude) with cost-aware routing
- 50+ integrated tools across Gmail, Notion, Google Drive, Telegram, Philips Hue, Tavily, Obsidian
- Average monthly API cost: **$8–10** vs. $20–30+ for equivalent n8n/Pro workflows
- Zero-downtime operation since deployment

**Tech stack:** Python, Kimi/Gemini/Claude APIs, IMAP/SMTP, Notion API, Google Drive API, Telegram Bot API, MCP protocol

---

### [Plaid Transaction Sync Engine](projects/plaid-sync/)

A local-first financial data pipeline that syncs bank transactions via Plaid API into an encrypted SQLite database. Handles idempotent delta syncs, soft-deleted audit trails, and automatic retry with exponential backoff.

**Key achievements:**
- **620+ transactions** synced in initial run across 6 accounts (checking, savings, credit, loan)
- **Idempotent verified:** Second sync added 0 duplicates — cursor-based delta tracking works
- **Atomic sync wrapping:** SQLite transaction ensures DB state and cursor advance together (no partial commits)
- **Soft-delete audit trail:** Removed transactions marked, not deleted — preserves reconciliation history
- **Encrypted at rest:** Plaid access tokens encrypted with Fernet, key isolated in `.env`
- **Sub-15-second sync time** for full delta across all accounts
- **Zero operational cost:** Plaid production API within free tier for personal use

**Tech stack:** Python 3.11, Plaid Python SDK, SQLite (WAL mode), cryptography (Fernet), tenacity, pydantic-settings

---

### [Home Infrastructure Stack](projects/infrastructure/)

A production-grade home server environment supporting development, automation, and media workflows.

**Key achievements:**
- MSI GE72VR (i7-7700HQ, 16GB, GTX1060) repurposed as 24/7 Ubuntu 24.04 server
- WSL2 + Ubuntu dual-environment with Git-backed configuration sync
- Full drive encryption, SSH key-only access, fail2ban, unattended-upgrades
- Ollama local LLM inference for privacy-sensitive and offline tasks
- Obsidian vault sync via Git + GitHub, with E2E encryption on mobile

**Tech stack:** Ubuntu Server 24.04, Docker, Ollama, Git, SSH, UFW, systemd

---

## Code Samples

| Sample | Language | Description |
|--------|----------|-------------|
| [model_router.py](code-samples/model_router.py) | Python | Multi-provider LLM fallback router with cost tracking |
| [email_triage.py](code-samples/email_triage.py) | Python | IMAP-based email classification and action queue |
| [sync_engine.py](code-samples/sync_engine.py) | Python | Atomic transaction sync with cursor management and soft-delete |
| [plaid_schema.sql](code-samples/plaid_schema.sql) | SQL | SQLite schema with WAL mode, foreign keys, audit trail |
| [threshold_alert.py](code-samples/threshold_alert.py) | Python | State-transition alerting to prevent notification fatigue |
| [git_sync.sh](code-samples/git_sync.sh) | Bash | Auto-resolve git sync with pull-before-push and retry logic |
| [himalaya.toml](code-samples/himalaya.toml) | TOML | Multi-account email CLI configuration (iCloud + Gmail) |

---

## Technical Writing

| Document | Topic |
|----------|-------|
| [Hermes Automation Pattern Library](docs/automation-patterns.md) | 10 reusable automation templates with cost analysis |
| [Model Selection & Fallback Matrix](docs/model-matrix.md) | LLM provider comparison: cost, latency, quality, task mapping |
| [Building Effective Agents: Lessons from Production](docs/agent-lessons.md) | Anti-patterns, cost control, and reliability strategies |

---

## Certifications & Education

| Certification | Status | Target |
|---------------|--------|--------|
| AWS Cloud Technical Essentials | Completed | 2025 |
| NDG Linux Essentials | In Progress | 2026 |
| LPI Linux Essentials | Planned | Late 2026 |
| CompTIA Linux+ | Planned | Mid 2027 |
| Red Hat Certified System Administrator (RHCSA) | Planned | Early 2028 |
| Docker & Kubernetes | Planned | Mid 2028 |
| AWS Solutions Architect Associate | Planned | 2028 |
| Terraform | Planned | 2028–2029 |
| Certified Kubernetes Administrator (CKA) | Planned | 2029 |
| CompTIA Security+ | Planned | 2029 |

**Education:** Harvard CS50P (Python) — In Progress  
**Scholarship:** Verizon Skill Forward / edX

*Removed from roadmap: CySA+, CS50x (not aligned with confirmed direction).*

---

## Metrics

- **Systems uptime:** 99%+ (self-hosted, self-monitored)
- **Automated tasks/day:** 100+ (email, finance, research, backup)
- **Financial records synced:** 620+ transactions, 6 accounts, 3+ months history
- **API cost efficiency:** $8–10/month for full automation stack
- **Lines of code written:** 3,500+ (Python, Bash, SQL, configs)
- **Repositories managed:** 4 (vault backup, portfolio, plaid-sync, private configs)

---

## Currently Building

- ✅ **Automated financial intelligence layer** — Plaid sync engine live, 620+ transactions tracked
- 🔧 Multi-inbox email triage (Gmail + iCloud via Himalaya CLI)
- 🔧 Local LLM integration (Ollama) for zero-cost inference tier
- 🔧 Claude Code + local model hybrid for software development
- 🔧 FastAPI dashboard for transaction browsing and custom financial reports
- 🔧 Spending anomaly detection with Telegram alerts

---

*Last updated: May 2026 | [View on GitHub](https://github.com/FvanW/portfolio)*
