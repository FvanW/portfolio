# Home Infrastructure Stack

> Production-grade server environment built from a repurposed gaming laptop. 24/7 operation, self-hosted, zero cloud dependency for core services.

---

## Hardware

| Component | Specification |
|-----------|--------------|
| **Machine** | MSI GE72VR 7RF Apache Pro |
| **CPU** | Intel i7-7700HQ (4C/8T) |
| **RAM** | 16GB DDR4 |
| **GPU** | NVIDIA GTX 1060 6GB (used for local LLM inference) |
| **Storage** | 256GB NVMe SSD (OS) + 1TB HDD (data) |
| **OS** | Ubuntu Server 24.04 LTS |
| **Uptime** | 24/7 since April 2025 |

---

## Network Architecture

```
Internet
   |
   | (Arris BGW210-700 Gateway)
   v
Port Forwarding: 22 (SSH), 443 (HTTPS)
   |
   v
┌───────────────────────────────────────────────────┐
│              MSI GE72VR (Ubuntu 24.04 Server)              │
│                                                              │
│   ┌───────────────────────────────────────────────────┐ │
│   │  Hermes Agent (Automation Engine)                    │ │
│   │  • 11 cron jobs                                      │ │
│   │  • Multi-provider LLM orchestration                  │ │
│   │  • 50+ integrated tools                              │ │
│   └───────────────────────────────────────────────────┘ │
│                                                              │
│   ┌───────────────────────────────────────────────────┐ │
│   │  Ollama (Local LLM Inference)                        │ │
│   │  • llama3.2, phi4, qwen2.5 models                    │ │
│   │  • Zero-cost inference tier                            │ │
│   │  • Privacy-sensitive task isolation                    │ │
│   └───────────────────────────────────────────────────┘ │
│                                                              │
│   ┌───────────────────────────────────────────────────┐ │
│   │  Docker Containers                                    │ │
│   │  • API gateway services                                │ │
│   │  • Isolated development environments                   │ │
│   └───────────────────────────────────────────────────┘ │
│                                                              │
└───────────────────────────────────────────────────┘
   |
   | (Local Network)
   v
┌───────────────────────────────────────────────────┐
│              Client Devices                                   │
│  • Lenovo Laptop (WSL2) — Daily driver, Obsidian Sync       │
│  • Pixel 10 Pro XL — Obsidian mobile, Telegram              │
│  • Philips Hue Bridge — Smart home integration              │
└───────────────────────────────────────────────────┘
```

---

## Security Configuration

| Layer | Implementation |
|-------|---------------|
| **Authentication** | SSH key-only (no password auth) |
| **Firewall** | UFW — ports 22, 80, 443 only |
| **Intrusion Prevention** | fail2ban (5 failed attempts = 1 hour ban) |
| **Updates** | unattended-upgrades for security patches |
| **Secrets Management** | Environment variables + restricted files (chmod 600) |
| **Network** | No direct root login, non-standard user accounts |
| **Backup** | Git-based configuration + cron-scheduled vault sync |

---

## Services

| Service | Port | Purpose |
|---------|------|---------|
| SSH | 22 | Remote administration |
| Hermes API Gateway | 8000 | Agent orchestration endpoint |
| Ollama | 11434 | Local LLM inference |
| Docker daemon | 2375 | Container management |

---

## Resource Utilization

| Metric | Typical | Peak |
|--------|---------|------|
| CPU | 5–15% | 60–80% (LLM inference) |
| RAM | 4–8 GB | 12–14 GB |
| Disk (OS) | 40% | 60% |
| Network | 1–5 Mbps | 20+ Mbps (model downloads) |
| Power | ~45W | ~90W (GPU active) |

---

## Key Achievements

- **Zero hardware investment:** Repurposed existing gaming laptop instead of buying a server
- **Full ownership:** No cloud subscriptions for core automation (only API usage for LLMs)
- **GPU utilization:** GTX 1060 runs local LLM inference at ~10–20 tokens/sec
- **Reliability:** 99%+ uptime with automatic recovery on power events
- **Remote management:** Fully administered via SSH from any device

---

## Skills Demonstrated

- Linux system administration (Ubuntu Server)
- Network configuration and security hardening
- Service orchestration and monitoring
- Hardware repurposing and optimization
- Power management and thermal optimization
- Remote access and VPN-less secure administration
