# 🛡️ AEGIS-SWARM
### Autonomous Emergency Ground Intelligence & Swarm Response System

<div align="center">
  <img src="https://img.shields.io/badge/Status-Operational_Deployable-3fb950?style=for-the-badge&logo=googlecloud" alt="Status" />
  <img src="https://img.shields.io/badge/Architecture-4_Agent_Cognitive_Mesh-00d2ff?style=for-the-badge&logo=openai" alt="Architecture" />
  <img src="https://img.shields.io/badge/Integration-Live_MCP_Telemetry-f0883e?style=for-the-badge&logo=nasa" alt="MCP" />
  <img src="https://img.shields.io/badge/Kaggle-Capstone_Project-20BEFF?style=for-the-badge&logo=Kaggle" alt="Kaggle" />
</div>

<br>

> **"Most AI systems answer questions. AEGIS-SWARM coordinates reality."** > An enterprise-grade AI operations command center that transforms raw drone/CCTV visual feeds and live environmental telemetry into a coordinated 3-step action plan within seconds.

---

## 🎥 The Command Center in Action
[![AEGIS-SWARM Pitch](https://img.shields.io/badge/YouTube-Watch_Pitch_Video-FF0000?style=for-the-badge&logo=youtube)](YOUR_YOUTUBE_LINK_HERE)

*soon.. ![Demo GIF](./docs/demo.gif)

---

## 🧠 The 4-Agent Cognitive Pipeline (ADK)

AEGIS-SWARM abandons the traditional "zero-shot LLM" approach. Instead, it utilizes a highly specialized, debating swarm of 4 agents powered by **Gemini 2.5 Flash**.

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
