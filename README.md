<div align="center">
<h1>⚔️ AEGIS-SWARM</h1>

### The AI That Refuses to Trust Its First Answer.

## One Image. Four Independent Minds. One Trusted Decision.

</div>

<p align="center">
<img src="https://readme-typing-svg.demolab.com?font=Orbitron&size=28&duration=2500&pause=800&color=00E5FF&center=true&vCenter=true&width=900&lines=OBSERVE.;ANALYZE.;CHALLENGE.;VALIDATE.;EXECUTE." />
</p>

<p align="center">

<img src="https://img.shields.io/badge/⚡_ENGINE-BUILT_FROM_SCRATCH-00C2FF?style=for-the-badge&labelColor=0D1117"/>
<img src="https://img.shields.io/badge/🧠_REASONING-CONSENSUS_BEFORE_ACTION-E53935?style=for-the-badge&labelColor=0D1117"/>
<img src="https://img.shields.io/badge/📡_PROTOCOL-REAL_MCP_SERVER-FF9800?style=for-the-badge&labelColor=0D1117"/>
<img src="https://img.shields.io/badge/🛡️_TRUST-CRITIC_VALIDATED-43A047?style=for-the-badge&labelColor=0D1117"/>
<img src="https://img.shields.io/badge/🔒_SECURITY-PRODUCTION_HARDENED-8B0000?style=for-the-badge&labelColor=0D1117"/>
<img src="https://img.shields.io/badge/☁️_DEPLOY-LIVE_ON_VERCEL_%2B_HF-4285F4?style=for-the-badge&logo=vercel&labelColor=0D1117"/>

</p>

<p align="center">
<img src="assets/demo.gif" width="100%">
</p>

> **Most AI systems generate answers. AEGIS-SWARM generates trusted operational decisions.**

AEGIS-SWARM is a custom-built multi-agent orchestration framework for **consensus-driven crowd safety intelligence**. Built for the *Agents for Good* track — because stampedes kill people, and single-model AI is not enough.

Every recommendation is debated, challenged, validated against a **real MCP protocol server** and live environmental telemetry, then — and only then — executed.

> **AEGIS-SWARM isn't an AI that tries to be smarter than other models. It's an engineering system designed to reduce the risk of acting on a single AI's mistake through consensus-driven reasoning, external evidence, and transparent decision validation.**
---

## 🌐 Live Demo

| Component | Platform | Link |
|---|---|---|
| **Frontend (Command Dashboard)** | Vercel | [aegis-swarm-tan.vercel.app](https://aegis-swarm-tan.vercel.app) |
| **Backend API (Swarm Engine)** | Hugging Face Spaces (Docker) | [coderudra-x-aegis-swarm-backend.hf.space](https://coderudra-x-aegis-swarm-backend.hf.space/api/analyze) |

> ⚠️ **Best experienced on desktop.** The Command 
> Dashboard is optimized for 1280px+ screen width. 
> Mobile browsers may have layout limitations.
> Open on laptop/PC for full experience.

---

## 🎥 The Command Center in Action

[![AEGIS-SWARM Pitch](https://img.shields.io/badge/YouTube-Watch_Pitch_Video-FF0000?style=for-the-badge&logo=youtube)](https://youtu.be/Hn5yP2FG8P4?si=muA6t49xStRKDXZY)

---

## ⚡ Why AEGIS-SWARM Exists

> **Crowd crushes are predictable. Kanjuruhan. Itaewon. Astroworld.**
>
> **They happen because no one trusted the data fast enough.**

Current crowd monitoring is reactive — a human watches a screen, notices a problem too late, and acts too slowly. AEGIS-SWARM makes the pipeline autonomous, multi-perspective, and **consensus-gated**: no action is taken until independent AI agents agree.

Instead of one model's first guess, every recommendation is:

- 👁️ **Observed** — Scout extracts spatial facts directly from raw pixels
- 🧠 **Analyzed** — Risk Agent classifies threat level from structured data
- ⚔️ **Challenged** — Critic Agent independently contests the assessment using live telemetry
- 🔁 **Debated** — If Critic disagrees, Risk re-evaluates with Critic's feedback (iterative loop)
- 🛡️ **Promoted** — Commander acts only after consensus is reached

<div align="center">

## **One Image. Four Independent Minds. One Trusted Decision.**

</div>

---

## 🧠 The 4-Agent Cognitive Pipeline

```mermaid
graph TD
    A["🖼️ Raw Drone/CCTV Image"] -->|Computer Vision| S["👁️ SCOUT AGENT\nVisual Extraction Only"]
    S -->|"JSON: people_count, density,\nblocked_paths, environment_type,\nhazard_factors"| R["⚠️ RISK AGENT\nBaseline Threat Assessment"]

    MCP["🛰️ MCP SERVER\nmcp_server.py · stdio transport\nOpen-Meteo Live API"] -->|"temperature, wind_speed\nvia JSON-RPC protocol"| C["⚖️ CRITIC AGENT\nIndependent Challenger"]

    R -->|"threat_level: HIGH/CRITICAL/..."| C

    C -->|"agrees_with_risk_level?"| D{"Consensus\nReached?"}
    D -- "❌ No — Override triggered\nCritic sends reasoning\nback to Risk" --> R
    D -- "✅ Yes — Max 2 iterations" --> CMD["♞ COMMANDER AGENT\nTactical Action Plan"]

    CMD -->|"immediate_actions[]\npersonnel_required: bool"| UI["🖥️ Live Command Dashboard\nNext.js Frontend"]

    classDef scout fill:#58a6ff,stroke:#58a6ff,stroke-width:2px,color:#fff;
    classDef risk fill:#3fb950,stroke:#3fb950,stroke-width:2px,color:#fff;
    classDef critic fill:#f85149,stroke:#f85149,stroke-width:2px,color:#fff;
    classDef cmd fill:#a371f7,stroke:#a371f7,stroke-width:2px,color:#fff;
    classDef mcp fill:#00d2ff,stroke:#00d2ff,stroke-width:2px,color:#000;
    classDef ui fill:#e3b341,stroke:#e3b341,stroke-width:2px,color:#000;

    class S scout;
    class R risk;
    class C critic;
    class CMD cmd;
    class MCP mcp;
    class UI ui;
```

### Agent Roles — Why Each One Exists

| Agent | Role | Why Separate? |
|---|---|---|
| **👁️ Scout** | Visual extraction only — no threat reasoning | Mixing vision + risk in one agent makes reasoning unauditable |
| **⚠️ Risk** | Baseline threat classification (LOW/MEDIUM/HIGH/CRITICAL) | First-pass assessor with no prior assumptions |
| **⚖️ Critic** | Independent challenger using live MCP telemetry | Prevents echo-chamber failure — explicitly prompted to disagree |
| **♞ Commander** | Tactical action plan from consensus-validated data | Acts on Critic's final verdict, not Risk's initial guess |

---

## 📡 The Real MCP Architecture

> **This is not a labeled REST call. This is actual Model Context Protocol.**

Most "MCP integrations" in hackathon projects are just `requests.get()` with "MCP" written in a comment. AEGIS-SWARM implements the real protocol:

```mermaid
sequenceDiagram
    participant Backend as 🖥️ server.py (MCP Client)
    participant MCP as 🛰️ mcp_server.py (MCP Server)
    participant API as 🌐 Open-Meteo API

    Backend->>MCP: Spawn subprocess (stdio transport)
    Backend->>MCP: JSON-RPC: initialize() handshake
    MCP-->>Backend: Protocol capabilities confirmed
    Backend->>MCP: call_tool("get_live_telemetry", {lat, lon})
    MCP->>API: HTTP GET /v1/forecast
    API-->>MCP: temperature, wind_speed
    MCP-->>Backend: JSON-RPC TextContent response
    Backend->>Backend: json.loads(result.content[0].text)
    Note over Backend: Live telemetry now in Critic Agent context
```

**`mcp_server.py`** — Standalone FastMCP server, exposed via `stdio` transport, registered tool `get_live_telemetry()` using official `mcp` Python SDK.

**`server.py`** — Acts as MCP client using `ClientSession` + `stdio_client`, performs protocol handshake via `session.initialize()`, calls tool via `session.call_tool()`.

This means the telemetry provider is **fully decoupled** — swappable, independently deployable, and reusable by any MCP-compatible host.

---

## ⚙️ Full System Architecture

```mermaid
flowchart LR
    subgraph Frontend ["🖥️ Vercel — Command Center UI"]
        Next["Next.js + Tailwind v4"]
        Upload["Drag & Drop Upload"]
    end

    subgraph Backend ["⚡ HF Spaces Docker — Swarm Engine"]
        Server["server.py\nOrchestrator"]
        subgraph Agents ["4-Agent Pipeline"]
            Scout["👁️ Scout"]
            Risk["⚠️ Risk"]
            Critic["⚖️ Critic"]
            Commander["♞ Commander"]
        end
        Security["🔒 Rate Limiter\nCORS Guard\nFile Validator"]
    end

    subgraph MCP_Layer ["📡 MCP Protocol Layer"]
        MCPServer["mcp_server.py\nstdio transport"]
        Weather["Open-Meteo\nLive API"]
    end

    Upload -->|"multipart/form-data\nimage/jpeg · png · webp\nmax 5MB"| Security
    Security --> Server
    Server --> Scout --> Risk --> Critic --> Commander
    Server <-->|"JSON-RPC\nstdio"| MCPServer
    MCPServer <-->|"HTTP"| Weather
    Commander -->|"Structured JSON"| Next
```

---

## 🔒 Security Architecture

Production-hardened from day one — not bolted on as an afterthought.

| Layer | Implementation | What It Prevents |
|---|---|---|
| **Rate Limiting** | `slowapi` — 10 req/min per IP on `/api/analyze` | DDoS, API quota exhaustion |
| **CORS Restriction** | Explicit allowlist (`localhost:3000` + Vercel URL only) | Cross-origin attacks from arbitrary domains |
| **File Type Validation** | Content-type check: `image/jpeg`, `image/png`, `image/webp` only | Arbitrary file injection into vision agent |
| **File Size Cap** | Hard 5MB limit, rejected before agent pipeline runs | Memory exhaustion attacks |
| **Path Traversal Guard** | `os.path.basename(file.filename)` on every upload | `../../server.py` overwrite attacks |
| **Privacy Cleanup** | `client.files.delete()` after Scout extraction (`finally` block) | Surveillance footage persisting on external servers |
| **API Key Guard** | Fail-fast `ValueError` if `GEMINI_API_KEY` missing | Silent auth failures masking misconfigurations |

---

## 🔁 The Debate Loop — How Consensus Actually Works

Most multi-agent systems are just sequential prompt chains. AEGIS-SWARM implements a **real iterative consensus mechanism**:

```
Iteration 1:
  Risk Agent → "MEDIUM threat. Moderate density in open area."
  Critic Agent → "Disagree. Environment is a stairway. Elevating to HIGH."
  → consensus_reached = False → loop back

Iteration 2 (with Critic's reasoning injected into Risk's context):
  Risk Agent → "HIGH threat. Stairway environment confirmed. Dense crowd."
  Critic Agent → "Agreed."
  → consensus_reached = True → Commander executes
```

- **Max 2 iterations** — prevents infinite cycling
- **Critic feedback injected** as `critic_override_reasoning` into Risk's next prompt
- **Commander only receives** the final consensus output — never an intermediate draft

---

## 🏆 Kaggle Rubric Fulfillment

| Concept | Implementation | Evidence |
|---|---|---|
| **Multi-Agent System** | 4-agent topology with iterative consensus debate loop | `server.py` — `while iteration < MAX_ITERATIONS` |
| **Real MCP Server** | `mcp_server.py` — FastMCP, `@mcp.tool()`, `stdio` transport, JSON-RPC | `mcp_server.py` + `get_telemetry_via_mcp()` in `server.py` |
| **Deployability** | Live on Vercel + Hugging Face Docker Spaces | [aegis-swarm-tan.vercel.app](https://aegis-swarm-tan.vercel.app) |
| **Security Features** | Rate limiting, CORS, file validation, path traversal guard, privacy cleanup | `server.py` + `test_main.py` |
| **Computer Vision** | Scout: Gemini vision model → structured Pydantic schema output | `agents/scout.py` |
| **Testing** | 8 pytest tests — security + parsing edge cases | `test_main.py` |

---

## 🚀 Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- Google Gemini API Key

### 1. Backend — Swarm Engine

```bash
cd CRX_Kaggriculture_Core

# Install all dependencies (includes MCP SDK)
pip install -r requirements.txt

# Configure environment
echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env

# Start the server (MCP server auto-spawns as subprocess)
python server.py
```

> Backend runs at `http://localhost:8000`

### 2. Frontend — Command Dashboard

```bash
cd aegis-frontend
npm install
npm run dev
```

> Frontend runs at `http://localhost:3000`

### 3. Run Tests

```bash
pytest test_main.py -v
```

### 4. Docker

```bash
docker build -t aegis-swarm .
docker run -p 8000:8000 --env-file .env aegis-swarm
```

### 5. Batch Processing

```bash
# Drop images into test_images/, reports saved to outputs/
python run_all.py
```

---

## 📁 Project Structure

```
AEGIS-SWARM/
├── agents/
│   ├── scout.py          # Visual extraction + privacy cleanup
│   ├── risk.py           # Baseline threat classification
│   ├── critic.py         # Independent challenger
│   └── commander.py      # Tactical action planner
├── mcp_server.py         # Real MCP server (FastMCP, stdio transport)
├── server.py             # FastAPI orchestrator + MCP client
├── main.py               # CLI runner (local debug)
├── run_all.py            # Batch image processor
├── test_main.py          # 8 pytest security + unit tests
├── Dockerfile            # Production container config
├── requirements.txt      # All dependencies including mcp SDK
└── aegis-frontend/       # Next.js command dashboard
```

---

## 👨‍💻 Developer

**Built by [CODERUDRA-X](https://github.com/CODERUDRA-X)**
*Building the future of AI, Vision Systems, and Defense-Tech.*

<p align="center">
<img src="https://img.shields.io/badge/Track-Agents_for_Good-00C2FF?style=for-the-badge&labelColor=0D1117"/>
<img src="https://img.shields.io/badge/Stack-Gemini_2.5_Flash-4285F4?style=for-the-badge&logo=google&labelColor=0D1117"/>
<img src="https://img.shields.io/badge/Protocol-Real_MCP_stdio-FF9800?style=for-the-badge&labelColor=0D1117"/>
<img src="https://img.shields.io/badge/Tests-8_Passing-43A047?style=for-the-badge&labelColor=0D1117"/>
<img src="https://img.shields.io/badge/Live-Deployed-00C2FF?style=for-the-badge&labelColor=0D1117"/>
</p>
