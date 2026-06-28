<div align="center">
<h1> AEGIS-SWARM </h1>

### The AI That Refuses to Trust Its First Answer.

## One Image. Four Independent Minds. One Trusted Decision.

</div>
<p align="center">

<img src="https://readme-typing-svg.demolab.com?font=Orbitron&size=28&duration=2500&pause=800&color=00E5FF&center=true&vCenter=true&width=900&lines=OBSERVE.;ANALYZE.;CHALLENGE.;VALIDATE.;EXECUTE." />

</p>

<p align="center">

<img src="https://img.shields.io/badge/⚡_ENGINE-BUILT_FROM_SCRATCH-00C2FF?style=for-the-badge&labelColor=0D1117"/>

<img src="https://img.shields.io/badge/🧠_REASONING-CONSENSUS_BEFORE_ACTION-E53935?style=for-the-badge&labelColor=0D1117"/>

<img src="https://img.shields.io/badge/📡_REALITY-LIVE_MCP_CONTEXT-FF9800?style=for-the-badge&labelColor=0D1117"/>

<img src="https://img.shields.io/badge/🛡️_TRUST-CRITIC_VALIDATED-43A047?style=for-the-badge&labelColor=0D1117"/>

<img src="https://img.shields.io/badge/☁️_DEPLOY-GOOGLE_CLOUD_RUN-4285F4?style=for-the-badge&logo=googlecloud&labelColor=0D1117"/>

</p>

<p align="center">
<img src="assets/demo.gif" width="100%">
</p>

**Autonomous Multi-Agent Visual Intelligence Framework**

> **Most AI systems generate answers. AEGIS-SWARM generates trusted operational decisions.**

AEGIS-SWARM is a custom-built multi-agent orchestration framework for consensus-driven visual intelligence. It was engineered from scratch to provide deterministic control over agent communication, debate, and decision validation rather than relying on a generic orchestration wrapper.

Every recommendation is debated, challenged, and validated against live environmental telemetry before execution.

**One image. Multiple AI minds. One trusted decision.**




---

## 🎥 The Command Center in Action
[![AEGIS-SWARM Pitch](https://img.shields.io/badge/YouTube-Watch_Pitch_Video-FF0000?style=for-the-badge&logo=youtube)](YOUR_YOUTUBE_LINK_HERE)

🚧 Demo video will be published before the Kaggle submission deadline.. ![Demo GIF](./docs/demo.gif)

---

## ⚡ Why AEGIS-SWARM?

> **Traditional AI trusts its first answer.**
>
> **AEGIS-SWARM doesn't.**

AEGIS-SWARM is a **consensus-driven multi-agent orchestration framework** engineered for high-stakes operational intelligence.

Instead of relying on a single model response, every recommendation is:

* 👁️ **Observed** through visual intelligence
* 🧠 **Analyzed** by specialized reasoning agents
* ⚔️ **Challenged** by an independent Critic Agent
* 📡 **Validated** against live environmental context (MCP)
* 🛡️ **Promoted** into an operational decision only after consensus

<div align="center">

## **One Image. Four Independent Minds. One Trusted Decision.**

</div>

 ## 🧠 The 4-Agent Cognitive Pipeline

Instead of relying on a single LLM response, AEGIS-SWARM orchestrates a team of specialized cognitive agents that observe, reason, challenge assumptions, and build consensus before recommending action.

```mermaid
graph TD
    A["Raw Drone/CCTV Image"] -->|Computer Vision| S["👁️ SCOUT AGENT"]
    S -->|JSON: Entities, Terrain, Hazards| R["🛡️ RISK AGENT"]

    M["🛰️ MCP GATEWAY"] -->|Live Weather & Wind Data| C["⚖️ CRITIC AGENT"]
    R -->|Baseline Threat Level| C

    C -->|Challenges Risk using Live Telemetry| D{Consensus Reached?}
    D -- No --> R
    D -- Yes --> CMD["♞ COMMANDER AGENT"]

    CMD -->|Final 3-Step Strategy| UI["Live Command Dashboard"]

    classDef scout fill:#58a6ff,stroke:#58a6ff,stroke-width:2px,color:#ffffff;
    classDef risk fill:#3fb950,stroke:#3fb950,stroke-width:2px,color:#ffffff;
    classDef critic fill:#f85149,stroke:#f85149,stroke-width:2px,color:#ffffff;
    classDef cmd fill:#a371f7,stroke:#a371f7,stroke-width:2px,color:#ffffff;
    classDef mcp fill:#00d2ff,stroke:#00d2ff,stroke-width:2px,color:#000000;

    class S scout;
    class R risk;
    class C critic;
    class CMD cmd;
    class M mcp;
```

---

## ⚙️ System Architecture & Deployability

Built on a decoupled, production-ready architecture designed for high-stakes environments.

```mermaid
flowchart LR
    subgraph Frontend [Command Center UI]
        Next[Next.js + Tailwind v4]
        Web[Drag & Drop Upload]
    end

    subgraph Backend [Swarm Engine]
        Fast[FastAPI Server]
        Agents[Gemini 2.5 ADK]
    end

    subgraph External [Reality Context]
        MCP[MCP: Open-Meteo API]
    end

    Web -->|multipart/form-data| Fast
    Fast --> Agents
    Agents <-->|Fetch Live Wind/Temp| MCP
    Agents -->|Structured JSON Response| Next

```

---

## 🏆 Kaggle Rubric Fulfillment

| Concept | Implementation in AEGIS-SWARM | Status |
| --- | --- | --- |
| **Agent / Multi-Agent System (ADK)** | Custom 4-agent topology (Scout, Risk, Critic, Commander) that debates and reaches consensus. | ✅ |
| **MCP Server / Tool Use** | Live HTTP integration fetching real-time environmental telemetry (Wind Speed, Temperature) to inform the Critic Agent. | ✅ |
| **Deployability** | Enterprise-grade decoupled architecture (FastAPI + Next.js). Codebase is ready for Google Cloud Run containerization. | ✅ |
| **Computer Vision / Spatial Reasoning** | The Scout agent does not rely on text prompts; it extracts spatial reality directly from raw pixels. | ✅ |

---

## 📸 Interface Gallery

---

## 🚀 Local Installation Guide

### Prerequisites

* Python 3.10+
* Node.js 18+
* Google Gemini API Key

### 1. Initialize the Swarm Backend (FastAPI)

```bash
cd CRX_Kaggriculture_Core

# Install Core Dependencies
pip install fastapi uvicorn python-multipart requests python-dotenv google-genai

# Configure Environment
echo "GEMINI_API_KEY=your_gemini_api_key_here" > .env

# Ignite the Server
python server.py

```

*Backend runs on `http://localhost:8000*`

### 2. Initialize the Command Center (Next.js)

```bash
cd aegis-frontend

# Install Dependencies
npm install

# Launch Dashboard
npm run dev

```

*Frontend runs on `http://localhost:3000*`

---

*Built with precision and intensity for the Kaggle Intensive Vibe Coding Capstone.*
