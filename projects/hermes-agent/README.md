# Hermes Agent — Personal AI Orchestration Platform

> A production-grade, self-hosted automation system that replaces paid platforms (n8n, Zapier) with custom Python, cron jobs, and multi-provider LLMs.

---

## Problem Statement

Off-the-shelf automation platforms charge $20–50+/month, require cloud dependencies, and force rigid workflow structures. I needed a system that was:
- **Free** (or near-free) to operate
- **Fully customizable** — no platform-imposed limits on logic complexity
- **Private** — personal financial data, emails, and family information never leaves my control
- **Resilient** — works offline, fails gracefully, and costs nothing when idle

**Solution:** Build a modular agent system from scratch, running 24/7 on a repurposed gaming laptop.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                        Hermes Agent Architecture                           │
├─────────────────────────────────────────────────────────────────────────────────────────────└
│                                                                            │
│   ┌──────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐     │
│   │  Trigger Layer   │      │   Scheduler    │      │   User Input   │     │
│   │  • Cron jobs      │      │   • systemd    │      │   • Telegram   │     │
│   │  • Webhooks       │ ──────▶ │   • Calendar   │ ──────▶ │   • CLI        │     │
│   └──────────────────┘      └─────────────────────┘      └─────────────────────┘     │
│                           │                                              │
│                           ▼                                              │
│   ┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│   │                         Orchestration Engine                           │
│   │  • Task routing & dispatch        • Error handling & retry logic         │
│   │  • Context window management      • Cost tracking & budget enforcement   │
│   └───────────────────────────────────────────────────────────────────────────────────────────────┘
│                           │                                              │
│         ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│         │   Kimi K2.6   │   │ Gemini 2.5  │   │  Claude S4   │   │ Perplexity  │   │   Ollama    │
│         │   (Primary)   │   │  (Fallback)  │   │  (Nuclear)   │   │  (Research)  │   │   (Local)   │
│         └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│   │                         Tool Ecosystem (50+ tools)                      │
│   │  📧 Email: Gmail (API), iCloud (IMAP), Himalaya CLI                     │
│   │  📋 Productivity: Notion (API + MCP), Google Drive, Obsidian Sync      │
│   │  📡 Communication: Telegram (Bot API), send_message                     │
│   │  🌐 Research: Tavily Search/Extract/Crawl, Perplexity Sonar Pro         │
│   │  🏠 Smart Home: Philips Hue (OpenHue CLI)                             │
│   │  💻 DevOps: Docker, GitHub, terminal, file management                   │
│   └───────────────────────────────────────────────────────────────────────────────────────────────┘
│                                                                            │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Active Automations

| Job | Schedule | Purpose | Monthly Cost |
|-----|----------|---------|-------------|
| Morning Digest | 04:00 daily | Weather, calendar, portfolio snapshot, daily brief | ~$0.30 |
| Evening Digest | 18:00 daily | Day wrap-up, financial close, task review | ~$0.30 |
| Gmail Deletion Handler | 06:30, 20:30 daily | Bulk-trash noise senders, preserve critical mail | ~$0.20 |
| Email Triage | Every 30 min | Classify unread mail, queue actions, post to Telegram | ~$1.50 |
| Financial Snapshot | 07:00 daily | Track XRP/ACHR/PLTR/TSP, debt payoff progress | ~$1.00 |
| Research Compiler | On-demand | Deep research via Tavily, synthesized brief | ~$1.00 |
| Inbox Zero Enforcement | 06:30, 20:30 daily | Archive known low-value senders | ~$0.50 |
| Git Workflow Reporter | 08:00 weekdays | PR/issue/CI status from GitHub | ~$0.50 |
| Smart Home Trigger | Sunset + manual | Philips Hue scene control | $0 |
| Threshold Alert | Every 2 hrs | Price alerts, state-transition only | ~$0.50 |
| Weekly Review | Sunday 18:00 | Aggregate week: finance, tasks, commits | ~$0.50 |
| **TOTAL** | | | **~$8–10/month** |

---

## Key Design Decisions

### 1. No Paid Automation Platform
Instead of n8n/Zapier ($20–50+/month), every workflow is a Python script triggered by cron. This gives full control over logic, error handling, and cost.

### 2. Multi-Provider LLM Fallback
No single vendor lock-in. Kimi K2.6 for reasoning, Gemini Flash for speed/vision, Claude Sonnet for quality assurance, Perplexity for research, Ollama for local privacy.

### 3. Deterministic + AI Hybrid
Simple tasks (email deletion, flag management) use deterministic rules. Complex tasks (classification, synthesis) use LLMs. Never use a $0.03 Claude call for a $0.000 regex operation.

### 4. Telegram as Universal Interface
All outputs route to Telegram channels: digests to one channel, documents to another, scripts to a third. No need to check 5 different apps.

### 5. GitHub as Single Source of Truth
Vault sync, configuration backups, and portfolio updates all flow through Git. Auto-push from MSI every 30 minutes, pull on Lenovo before editing.

---

## Outcomes

- **Cost reduction:** $8–10/month vs. $30–50+ for equivalent n8n/Pro workflows
- **Privacy:** Personal financial data, emails, and family information never leaves owned infrastructure
- **Reliability:** 99%+ uptime on self-hosted hardware; graceful degradation when APIs are down
- **Skill development:** Production experience with Python, API integration, Linux server administration, LLM orchestration, and MCP protocol
- **Scalability:** New automations take 30–60 minutes to implement vs. hours of platform configuration

---

## Files

- [Architecture & Usage Guide](../../docs/hermes-architecture.md) — Full system documentation
- [Automation Pattern Library](../../docs/automation-patterns.md) — 10 reusable templates
- [Model Selection Matrix](../../docs/model-matrix.md) — Provider comparison and routing logic
- [Code Samples](../../code-samples/) — Python implementations
