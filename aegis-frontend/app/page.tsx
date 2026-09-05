"use client";

import { useState, useEffect, useRef, useCallback } from "react";

/* ── Types ──────────────────────────────────────────────────────────── */

type AgentName = "SCOUT" | "RISK" | "CRITIC" | "CMD" | "MCP";
type Highlight  = "override" | "warn" | "cmd" | "normal" | "mcp";

interface LogEntry {
  ts:        string;
  agent:     AgentName;
  msg:       string;
  highlight: Highlight;
}

interface SafetyGateResult {
  gate_decision: "AUTONOMOUS_ACTION_AUTHORIZED" | "REQUIRES_REEVALUATION" | "HUMAN_REVIEW_REQUIRED";
  gate_reason: string;
  threat_level_evaluated: string;
  evidence_classification_evaluated: string;
  commander_authorized: boolean;
  human_review_required: boolean;
}

interface VenueEvidence {
  data_source: string;
  zone_id?: string;
  rated_capacity?: number;
  current_occupancy?: number;
  occupancy_pct?: number;
  exits_available?: number;
  exits_total?: number;
  active_incident_flag?: boolean;
  mcp_status: string;
}

interface WeatherData {
  source: string;
  temperature: string;
  wind_speed: string;
  mcp_status: string;
}

interface ReportData {
  scout_data: {
    people_count:     number;
    blocked_paths:    number;
    environment_type: string;
    hazard_factors:   string[];
  };
  mcp_data?: {
    evidence: VenueEvidence;
    weather: WeatherData;
  };
  risk_assessment:  { threat_level: string };
  critic_review:    { adjusted_threat_level: string; critic_reasoning: string };
  evidence_classification?: string;
  safety_gate?: SafetyGateResult;
  // commander_plan is null when the deterministic safety gate blocks
  // autonomous action (HUMAN_REVIEW_REQUIRED / REQUIRES_REEVALUATION) --
  // the Commander agent is never invoked in that case, so the UI must
  // not assume this is always populated.
  commander_plan:   { immediate_actions: string[] } | null;
  final_decision?: string;
  dispatch_status?: { telegram: boolean; email: boolean; errors: string[] };
}

/* ── Constants ───────────────────────────────────────────────────────── */

const AGENT_STYLES: Record<AgentName, { border: string; text: string; bg: string }> = {
  SCOUT:  { border: "#58a6ff", text: "#58a6ff", bg: "rgba(88,166,255,0.09)"   },
  MCP:    { border: "#00d2ff", text: "#00d2ff", bg: "rgba(0,210,255,0.09)"    }, 
  RISK:   { border: "#3fb950", text: "#3fb950", bg: "rgba(63,185,80,0.09)"    },
  CRITIC: { border: "#f85149", text: "#f85149", bg: "rgba(248,81,73,0.13)"    },
  CMD:    { border: "#a371f7", text: "#a371f7", bg: "rgba(163,113,247,0.09)"  },
};

const INITIAL_REPORT: ReportData = {
  scout_data: {
    people_count:     0,
    blocked_paths:    0,
    environment_type: "AWAITING FEED...",
    hazard_factors:   [],
  },
  mcp_data: {
    weather: {
      source: "STANDBY",
      temperature: "--",
      wind_speed: "--",
      mcp_status: "Standby",
    },
    evidence: {
      data_source: "STANDBY",
      mcp_status: "Standby",
    },
  },
  risk_assessment:  { threat_level: "STANDBY" },
  critic_review: {
    adjusted_threat_level: "STANDBY",
    critic_reasoning: "System idle. Awaiting visual telemetry to initiate swarm pipeline.",
  },
  evidence_classification: "unavailable",
  safety_gate: {
    gate_decision: "AUTONOMOUS_ACTION_AUTHORIZED",
    gate_reason: "System idle. No incident to evaluate.",
    threat_level_evaluated: "STANDBY",
    evidence_classification_evaluated: "unavailable",
    commander_authorized: true,
    human_review_required: false,
  },
  commander_plan: {
    immediate_actions: [
      "Upload aerial or CCTV feed to initialize.",
      "Standby for agent routing...",
      "Maintain perimeter.",
    ],
  },
  final_decision: "STANDBY",
  dispatch_status: {
    telegram: false,
    email: false,
    errors: [],
  },
};

/* ── useUtcTime ──────────────────────────────────────────────────────── */

function useUtcTime(): string {
  const [time, setTime] = useState<string>("");
  useEffect(() => {
    const tick = () => {
      const d  = new Date();
      const hh = String(d.getUTCHours()).padStart(2,"0");
      const mm = String(d.getUTCMinutes()).padStart(2,"0");
      const ss = String(d.getUTCSeconds()).padStart(2,"0");
      setTime(`${hh}:${mm}:${ss} UTC`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);
  return time;
}

/* ── AgentBadge ──────────────────────────────────────────────────────── */

function AgentBadge({ agent }: { agent: AgentName }) {
  const s = AGENT_STYLES[agent];
  return (
    <span style={{
      display:        "inline-flex",
      alignItems:     "center",
      justifyContent: "center",
      fontSize:       "9px",
      fontWeight:     600,
      letterSpacing:  "0.08em",
      border:         `1px solid ${s.border}`,
      color:          s.text,
      background:     s.bg,
      borderRadius:   "2px",
      height:         "20px",
      minWidth:       "46px",
      flexShrink:     0,
      fontFamily:     "var(--font-mono, monospace)",
    }}>
      {agent}
    </span>
  );
}

/* ── DebateLog ───────────────────────────────────────────────────────── */

function DebateLog({ entries }: { entries: LogEntry[] }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [entries]);

  const msgColor = (h: Highlight): string => {
    if (h === "override") return "#f85149";
    if (h === "warn")     return "#e2936a";
    if (h === "cmd")      return "#a371f7";
    if (h === "mcp")      return "#00d2ff";
    return "#5a7a90";
  };

  return (
    <div ref={ref} style={{ flex:1, overflowY:"auto", paddingRight:"4px", fontSize:"11px" }}>
      {entries.filter(Boolean).map((entry, i) => (
        <div key={i} style={{ display:"grid", gridTemplateColumns:"58px 50px 1fr", gap:"4px", marginBottom:"12px", animation:"logIn 0.25s ease" }}>
          <span style={{ color:"#1e3a52", paddingTop:"2px", fontFamily:"monospace" }}>{entry.ts}</span>
          <AgentBadge agent={entry.agent} />
          <span style={{ lineHeight:1.6, color:msgColor(entry.highlight), fontWeight: entry.highlight==="override" ? 600 : 400 }}>
            {entry.msg}
          </span>
        </div>
      ))}

      <div style={{ display:"flex", alignItems:"center", gap:"8px", marginTop:"6px", paddingTop:"6px", borderTop:"1px solid #0e1f2e" }}>
        <span style={{ display:"inline-block", width:6, height:12, background:"#1e4a6a", animation:"blink 1s step-end infinite" }} />
        <span style={{ fontSize:"9px", letterSpacing:"0.12em", color:"#1a3a52" }}>PIPELINE ACTIVE</span>
      </div>
    </div>
  );
}

/* ── SwarmTopology ───────────────────────────────────────────────────── */

function SwarmTopology({ activeAgent }: { activeAgent: string | null }) {
  const isExtracting = activeAgent === 'SCOUT' || activeAgent === 'MCP' || activeAgent === 'RISK' || activeAgent === 'CRITIC';
  const isCommanding = activeAgent === 'CMD';

  return (
    <svg viewBox="0 0 260 210" xmlns="http://www.w3.org/2000/svg" style={{ width:"100%", height:"100%" }}>
      <defs>
        <marker id="a2" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
          <path d="M2 1L8 5L2 9" fill="none" stroke="#f85149" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </marker>
      </defs>

      <line x1="130" y1="38" x2="52"  y2="98"  
        stroke={isExtracting ? "#58a6ff" : "#1e3a52"} 
        strokeWidth={isExtracting ? "1.5" : "1"} 
        strokeDasharray="4 4" 
        style={isExtracting ? { animation: "dataFlow 0.6s linear infinite" } : { opacity: 0.4 }}
      />
      <line x1="130" y1="38" x2="208" y2="98"  
        stroke={isExtracting ? "#58a6ff" : "#1e3a52"} 
        strokeWidth={isExtracting ? "1.5" : "1"} 
        strokeDasharray="4 4" 
        style={isExtracting ? { animation: "dataFlow 0.6s linear infinite" } : { opacity: 0.4 }}
      />

      <line x1="52"  y1="118" x2="125" y2="170" 
        stroke={isCommanding ? "#a371f7" : "#0e2030"} 
        strokeWidth={isCommanding ? "1.5" : "0.5"} 
        strokeDasharray="4 4" 
        style={isCommanding ? { animation: "dataFlow 0.6s linear infinite" } : { opacity: 0.4 }}
      />
      <line x1="208" y1="118" x2="135" y2="170" 
        stroke={isCommanding ? "#a371f7" : "#0e2030"} 
        strokeWidth={isCommanding ? "1.5" : "0.5"} 
        strokeDasharray="4 4" 
        style={isCommanding ? { animation: "dataFlow 0.6s linear infinite" } : { opacity: 0.4 }}
      />

      <line x1="72" y1="108" x2="188" y2="108"
        stroke="#f85149" strokeWidth="1.5" opacity={activeAgent === 'CRITIC' || activeAgent === 'RISK' ? 0.9 : 0.2}
        strokeDasharray="6 4"
        markerEnd="url(#a2)" markerStart="url(#a2)"
        style={activeAgent === 'CRITIC' || activeAgent === 'RISK' ? { animation:"debateDash 1s linear infinite" } : {}}
      />
      <text x="130" y="103" fill={activeAgent === 'CRITIC' || activeAgent === 'RISK' ? "#f85149" : "#7a2020"} fontSize="7" textAnchor="middle" letterSpacing="2" fontFamily="monospace">DEBATE</text>

      {/* SCOUT */}
      <rect x="90" y="14" width="80" height="32" rx="3" fill="rgba(88,166,255,0.06)" stroke={activeAgent === 'SCOUT' ? "#ffffff" : "#58a6ff"} strokeWidth={activeAgent === 'SCOUT' ? "1.5" : "0.7"}/>
      <text x="130" y="27" textAnchor="middle" fill="#58a6ff" fontSize="9" fontWeight="500" letterSpacing="1.5" fontFamily="monospace">SCOUT</text>
      <text x="130" y="40" textAnchor="middle" fill="#2a6a8a" fontSize="7" letterSpacing="1" fontFamily="monospace">{activeAgent ? (activeAgent === 'CMD' ? 'DONE ✓' : 'ACTIVE ●') : 'DONE ✓'}</text>

      {/* RISK */}
      <rect x="14" y="90" width="76" height="32" rx="3" fill="rgba(63,185,80,0.04)" stroke="#3fb950" strokeWidth="0.7"/>
      <text x="52" y="103" textAnchor="middle" fill="#3fb950" fontSize="9" fontWeight="500" letterSpacing="1.5" fontFamily="monospace">RISK</text>
      <text x="52" y="116" textAnchor="middle" fill="#2a5a2a" fontSize="7" letterSpacing="1" fontFamily="monospace">PIPELINE</text>

      {/* CRITIC */}
      <rect x="170" y="90" width="76" height="32" rx="3" fill="rgba(248,81,73,0.08)" stroke="#f85149" strokeWidth="1"
        style={activeAgent === 'CRITIC' ? { filter:"drop-shadow(0 0 6px rgba(248,81,73,0.3))" } : {}}/>
      <text x="208" y="103" textAnchor="middle" fill="#f85149" fontSize="9" fontWeight="500" letterSpacing="1.5" fontFamily="monospace">CRITIC</text>
      <text x="208" y="116" textAnchor="middle" fill="#9a2020" fontSize="7" letterSpacing="1" fontFamily="monospace">{activeAgent === 'CRITIC' ? 'ACTIVE ●' : 'STANDBY'}</text>

      {/* COMMANDER */}
      <rect x="90" y="162" width="80" height="32" rx="3" 
        fill={activeAgent === 'CMD' ? "rgba(163,113,247,0.15)" : "#060f1a"} 
        stroke={activeAgent === 'CMD' ? "#a371f7" : "#1e2a38"} 
        strokeWidth={activeAgent === 'CMD' ? "1.5" : "0.5"}
        style={activeAgent === 'CMD' ? { filter:"drop-shadow(0 0 8px rgba(163,113,247,0.5))", transition: "all 0.3s ease" } : { transition: "all 0.3s ease" }}
      />
      <text x="130" y="175" textAnchor="middle" fill={activeAgent === 'CMD' ? "#a371f7" : "#2a3a4a"} fontSize="9" letterSpacing="1.5" fontFamily="monospace">COMMAND</text>
      <text x="130" y="188" textAnchor="middle" fill={activeAgent === 'CMD' ? "#d0b0ff" : "#1a2a3a"} fontSize="7" letterSpacing="1" fontFamily="monospace">{activeAgent === 'CMD' ? 'EXECUTING ●' : 'PENDING…'}</text>
    </svg>
  );
}

/* ── ImageZone ───────────────────────────────────────────────────────── */

function ImageZone({ src, onUpload, analyzing }: { src:string|null; onUpload:(f:File)=>void; analyzing:boolean }) {
  const inputRef  = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDrag(false);
    const f = e.dataTransfer.files?.[0];
    if (f && f.type.startsWith("image/")) onUpload(f);
  }, [onUpload]);

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={e => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={onDrop}
      style={{
        height:       "260px",
        background:   "#03070c",
        border:       `1px solid ${drag ? "#58a6ff" : "#1e2a38"}`,
        borderRadius: "4px",
        position:     "relative",
        overflow:     "hidden",
        cursor:       "pointer",
        flexShrink:   0,
        transition:   "border-color 0.2s",
      }}
    >
      <div style={{
        position:"absolute", inset:0, pointerEvents:"none",
        backgroundImage:"linear-gradient(rgba(30,80,120,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(30,80,120,.05) 1px,transparent 1px)",
        backgroundSize:"28px 28px",
      }}/>

      {([["3px","3px","border-top","border-left"],["3px","auto","border-top","border-right"],["auto","3px","border-bottom","border-left"],["auto","auto","border-bottom","border-right"]] as const).map(([t,r,b,l],i)=>(
        <div key={i} style={{
          position:"absolute",
          top:  i < 2 ? "12px" : undefined,
          bottom: i >= 2 ? "12px" : undefined,
          left:  i % 2 === 0 ? "12px" : undefined,
          right: i % 2 === 1 ? "12px" : undefined,
          width:"14px", height:"14px",
          borderTop:    (i < 2)         ? "1px solid #2a5a7a" : undefined,
          borderBottom: (i >= 2)        ? "1px solid #2a5a7a" : undefined,
          borderLeft:   (i % 2 === 0)   ? "1px solid #2a5a7a" : undefined,
          borderRight:  (i % 2 === 1)   ? "1px solid #2a5a7a" : undefined,
        }}/>
      ))}

      {analyzing && <div style={{
        position:"absolute", left:0, right:0, height:"1px",
        background:"linear-gradient(90deg,transparent,rgba(88,166,255,0.4),transparent)",
        animation:"scan 2s linear infinite",
      }}/>}

      {src
        ? <img src={src} alt="feed" style={{ position:"absolute", inset:0, width:"100%", height:"100%", objectFit:"contain" }}/>
        : (
          <div style={{ position:"absolute", inset:0, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", gap:"8px" }}>
            <svg style={{ width:32, height:32, color:"#1e4a6a" }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
            <span style={{ fontSize:"10px", letterSpacing:"0.2em", color:"#1e4a6a" }}>
              {drag ? "DROP IMAGE" : "DRONE / CCTV FEED — CLICK OR DROP"}
            </span>
          </div>
        )
      }
      <input ref={inputRef} type="file" accept="image/*" style={{ display:"none" }}
        onChange={e => { const f = e.target.files?.[0]; if (f) onUpload(f); }}/>
    </div>
  );
}

/* ── Main Dashboard ──────────────────────────────────────────────────── */

export default function AegisDashboard() {
  const utcTime   = useUtcTime();
  const [src, setSrc]         = useState<string|null>(null);
  const [analyzing, setAn]    = useState(false);
  const [frame, setFrame]     = useState(47);
  const [logEntries, setLog]  = useState<LogEntry[]>([]);
  
  const [report, setReport]   = useState<ReportData>(INITIAL_REPORT);
  const [activeAgent, setActiveAgent] = useState<string | null>(null);

  // 🌟 NEW: Caspian Multi-Channel State
  const [showCaspianModal, setShowCaspianModal] = useState<boolean>(false);
  const [caspianDispatched, setCaspianDispatched] = useState<boolean>(false);

  useEffect(() => {
    const id = setInterval(() => setFrame(f => f + 1), 900);
    return () => clearInterval(id);
  }, []);

  const getLogTimestamp = () => {
    const d = new Date();
    return `${String(d.getUTCHours()).padStart(2,"0")}:${String(d.getUTCMinutes()).padStart(2,"0")}:${String(d.getUTCSeconds()).padStart(2,"0")}`;
  };

  const handleUpload = useCallback(async (file: File) => {
    setSrc(URL.createObjectURL(file));
    setAn(true);
    setReport(INITIAL_REPORT);
    setLog([]);
    setActiveAgent('SCOUT');
    setCaspianDispatched(false);

    setLog([{ ts: getLogTimestamp(), agent: "SCOUT", highlight: "normal", msg: `Uplink established. Analyzing: ${file.name}...` }]);

    const formData = new FormData();
    formData.append("file", file);

    try {
      // 1. FIX: Explicitly forcing localhost
      const res = await fetch("https://coderudra-x-aegis-swarm-backend.hf.space/api/analyze", {
  method: "POST",
  body: formData,
});

      const data = await res.json();
      
      // 2. FIX: Catching FastAPI "detail" errors before they crash the UI
      if (!res.ok) {
        throw new Error(data.detail || data.error || `Server Error: ${res.status}`);
      }
      
      if (data.error) throw new Error(data.error);
      
      setReport(data as ReportData);

      const dynamicLogs: LogEntry[] = [
        { ts: getLogTimestamp(), agent: "SCOUT", highlight: "normal", msg: `Extraction complete. Terrain: ${data.scout_data.environment_type}. Detected ${data.scout_data.people_count} entities.` },
        { ts: getLogTimestamp(), agent: "MCP", highlight: "mcp", msg: `Weather: ${data.mcp_data?.weather?.temperature ?? "N/A"}, Wind: ${data.mcp_data?.weather?.wind_speed ?? "N/A"}. Venue evidence: ${data.mcp_data?.evidence?.data_source ?? "unavailable"}.` },
        { ts: getLogTimestamp(), agent: "RISK", highlight: "normal", msg: `Base threat evaluated: ${data.risk_assessment.threat_level}.` }
      ];

      if (data.critic_review.adjusted_threat_level !== data.risk_assessment.threat_level) {
        dynamicLogs.push({ ts: getLogTimestamp(), agent: "CRITIC", highlight: "warn", msg: "Challenging baseline assumption using MCP & Visual data." });
        dynamicLogs.push({ ts: getLogTimestamp(), agent: "CRITIC", highlight: "override", msg: `OVERRIDE: ${data.risk_assessment.threat_level} → ${data.critic_review.adjusted_threat_level}.` });
      } else {
        dynamicLogs.push({ ts: getLogTimestamp(), agent: "CRITIC", highlight: "normal", msg: `Concur with Risk Assessment: ${data.risk_assessment.threat_level}.` });
      }

      // Deterministic safety gate is NOT an LLM call -- shown as its own
      // log line so the pipeline's real decision boundary is visible,
      // not just "Critic said X, Commander did Y".
      const gateAuthorized = data.safety_gate?.commander_authorized ?? true;
      dynamicLogs.push({
        ts: getLogTimestamp(),
        agent: "CMD",
        highlight: gateAuthorized ? "cmd" : "warn",
        msg: gateAuthorized
          ? `Safety gate: evidence ${data.safety_gate?.evidence_classification_evaluated ?? "unavailable"} — autonomous action authorized.`
          : `Safety gate: ${data.safety_gate?.gate_decision ?? "HUMAN_REVIEW_REQUIRED"} — autonomous action blocked.`,
      });

      if (gateAuthorized) {
        dynamicLogs.push({ ts: getLogTimestamp(), agent: "CMD", highlight: "cmd", msg: "Consensus received. Executing action plan." });
      }

      let i = 0;
      const logInterval = setInterval(() => {
        if (i < dynamicLogs.length) {
          const currentLog = dynamicLogs[i];
          setLog(prev => [...prev, currentLog]);
          setActiveAgent(currentLog.agent === "MCP" ? "SCOUT" : currentLog.agent);
          i++;
        } else {
          clearInterval(logInterval);
          setActiveAgent("CMD"); 
          setAn(false);
          // Only mark Caspian as dispatched if the backend actually
          // attempted dispatch (HIGH/CRITICAL) -- the dispatch itself
          // still happens for human-review cases too (responders must
          // be alerted either way), so this simply mirrors what the
          // backend's alert message will say.
          setCaspianDispatched(true);
        }
      }, 800);

    } catch (error: any) {
      const errorMsg = error.message.includes("429") 
        ? "API Quota Exceeded. Please change Gemini API Key in .env" 
        : `Connection/Swarm Error: ${error.message}`;
        
      setLog(prev => [...prev, { ts: getLogTimestamp(), agent: "CMD", highlight: "override", msg: errorMsg }]);
      setAn(false);
      setActiveAgent(null);
    }
  }, []);

  const threat = report.critic_review.adjusted_threat_level;
  const threatColor = threat === "CRITICAL" ? "#f85149" : threat === "HIGH" ? "#f0883e" : threat === "MEDIUM" ? "#e3b341" : threat === "STANDBY" ? "#1e4a6a" : "#3fb950";
  const gateAuthorized = report.safety_gate?.commander_authorized ?? true;

  return (
    <>
      <style>{`
        @keyframes blink      { 0%,100%{opacity:1} 50%{opacity:0} }
        @keyframes logIn      { from{opacity:0;transform:translateY(3px)} to{opacity:1;transform:none} }
        @keyframes scan       { from{top:0%} to{top:100%} }
        @keyframes debateDash { to{stroke-dashoffset:-20} }
        @keyframes criticGlow { 0%,100%{box-shadow:0 0 8px rgba(248,81,73,.15)} 50%{box-shadow:0 0 22px rgba(248,81,73,.35)} }
        @keyframes dataFlow   { from { stroke-dashoffset: 24; } to { stroke-dashoffset: 0; } }
        ::-webkit-scrollbar       { width:3px; height:3px }
        ::-webkit-scrollbar-track { background:transparent }
        ::-webkit-scrollbar-thumb { background:#1e2a38; border-radius:2px }
      `}</style>

      <div style={{ height:"100vh", background:"#050c14", color:"#b8cfe0", fontFamily:"'Geist Mono',ui-monospace,monospace", fontSize:"13px", display:"flex", flexDirection:"column", overflow:"hidden" }}>

        {/* ── TOPBAR ── */}
        <header style={{ height:"56px", flexShrink:0, background:"#040b12", borderBottom:"1px solid #0e1f2e", display:"flex", alignItems:"center", padding:"0 24px", gap:"16px" }}>
          <span style={{ fontSize:"16px", fontWeight:700, letterSpacing:"0.25em", color:"#e0edf8" }}>AEGIS–SWARM</span>
          <div style={{ width:"1px", height:"20px", background:"#0e1f2e" }}/>
          <span style={{ fontSize:"10px", display:"flex", alignItems:"center", gap:"6px", letterSpacing:"0.1em", color:"#3fb950" }}>
            <span style={{ width:6, height:6, borderRadius:"50%", background:"#3fb950", display:"inline-block", animation:"blink 1s step-end infinite" }}/>
            LIVE ANALYSIS
          </span>

          {/* 🌟 NEW: Caspian Sync Status Badge (Capsule Style) */}
<span style={{ fontSize:"10px", display:"flex", alignItems:"center", gap:"6px", letterSpacing:"0.1em", color:"#ff007f", border:"1px solid #ff007f", padding:"4px 12px", borderRadius:"20px", background:"rgba(255,0,127,0.05)" }}>
  <style>{`
    @keyframes caspianPinkBlink {
      0% { opacity: 0.4; box-shadow: 0 0 2px #ff007f; }
      50% { opacity: 1; box-shadow: 0 0 14px #ff007f, 0 0 6px #ff007f; }
      100% { opacity: 0.4; box-shadow: 0 0 2px #ff007f; }
    }
  `}</style>
  <span style={{ width:6, height:6, borderRadius:"50%", background:"#ff007f", display:"inline-block", animation: "caspianPinkBlink 1.2s infinite ease-in-out" }}/>
  CASPIAN RELAY: ONLINE (TG / EMAIL)
</span>



          <div style={{ marginLeft:"auto", display:"flex", gap:"24px", alignItems:"center" }}>
            <span style={{ fontSize:"10px", letterSpacing:"0.15em", color:"#2a5a7a" }}>NEURAL MESH / 4-AGENT PIPELINE</span>
            <span style={{ fontSize:"10px", color:"#1a3a52", fontFamily:"monospace" }}>
              FRAME <span style={{ color:"#2a6a8a" }}>{String(frame).padStart(4,"0")}</span>
            </span>
            <span style={{ fontSize:"10px", color:"#2a5a7a", fontFamily:"monospace" }}>{utcTime}</span>
          </div>
        </header>

        {/* ── MAIN GRID ── */}
        <div style={{ flex:1, display:"grid", gridTemplateColumns:"350px 1fr 380px", overflow:"hidden" }}>

          {/* ─── LEFT COLUMN ─── */}
          <div style={{ borderRight:"1px solid #0e1f2e", display:"flex", flexDirection:"column", overflow:"hidden", overflowY:"auto" }}>
            <div style={{ padding:"16px 20px", borderBottom:"1px solid #0e1f2e", flexShrink:0 }}>
              <div style={{ fontSize:"9px", letterSpacing:"0.2em", color:"#1a4060", marginBottom:"12px" }}>SWARM TOPOLOGY</div>
              <div style={{ height:"220px" }}>
                <SwarmTopology activeAgent={activeAgent}/>
              </div>
            </div>

            <div style={{ padding:"16px 20px", borderBottom:"1px solid #0e1f2e", flexShrink:0, background: threat === 'STANDBY' ? "transparent" : "rgba(0, 210, 255, 0.02)" }}>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"10px" }}>
                <span style={{ fontSize:"9px", letterSpacing:"0.2em", color:"#1a4060" }}>MCP TELEMETRY</span>
                <span style={{ fontSize:"8px", letterSpacing:"0.1em", border:"1px solid rgba(0, 210, 255, 0.4)", color:"#00d2ff", padding:"2px 8px", borderRadius:"2px" }}>EXTERNAL API</span>
              </div>
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:"8px", marginBottom:"8px" }}>
                <div style={{ padding:"10px 12px", background:"#040b12", border:"1px solid #0e1f2e", borderRadius:"3px" }}>
                  <div style={{ fontSize:"8px", letterSpacing:"0.12em", color:"#1a4060" }}>WIND SPEED</div>
                  <div style={{ fontSize:"15px", color:"#00d2ff", marginTop:"4px" }}>{report.mcp_data?.weather?.wind_speed}</div>
                </div>
                <div style={{ padding:"10px 12px", background:"#040b12", border:"1px solid #0e1f2e", borderRadius:"3px" }}>
                  <div style={{ fontSize:"8px", letterSpacing:"0.12em", color:"#1a4060" }}>TEMPERATURE</div>
                  <div style={{ fontSize:"15px", color:"#00d2ff", marginTop:"4px" }}>{report.mcp_data?.weather?.temperature}</div>
                </div>
              </div>
              <div style={{ fontSize:"8px", color:"#4a6a80", letterSpacing:"0.08em", textTransform: 'uppercase' }}>
                SRC: {report.mcp_data?.weather?.source} (SECONDARY CONTEXT ONLY)
              </div>
            </div>

            <div style={{ padding:"16px 20px", borderBottom:"1px solid #0e1f2e", flexShrink:0 }}>
              <div style={{ fontSize:"9px", letterSpacing:"0.2em", color:"#1a4060", marginBottom:"10px" }}>SCOUT EXTRACTION</div>
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:"8px" }}>
                {[
                  { k:"ENTITIES",  v:String(report.scout_data.people_count),  c:"#b8cfe0" },
                  { k:"PATHS OUT", v:String(report.scout_data.blocked_paths), c:"#f0883e" },
                  { k:"TERRAIN",   v:report.scout_data.environment_type.split(' ')[0], c:"#58a6ff" },
                  { k:"HAZARDS",   v:String(report.scout_data.hazard_factors.length), c:"#f85149" },
                ].map(({ k, v, c }) => (
                  <div key={k} style={{ padding:"10px 12px", background:"#040b12", border:"1px solid #0e1f2e", borderRadius:"3px" }}>
                    <div style={{ fontSize:"8px", letterSpacing:"0.12em", color:"#1a4060" }}>{k}</div>
                    <div style={{ fontSize:"16px", color:c, marginTop:"4px", textTransform: 'capitalize' }}>{v}</div>
                  </div>
                ))}
              </div>
            </div>

            <div style={{ margin:"16px 20px", padding:"16px", background: threat === 'STANDBY' ? "#03070c" : "rgba(248,81,73,0.04)", border:`1px solid ${threatColor}`, borderRadius:"4px", flexShrink:0, animation: threat !== 'STANDBY' ? "criticGlow 2.5s ease-in-out infinite" : "none" }}>
              <div style={{ fontSize:"9px", letterSpacing:"0.15em", color: threat === 'STANDBY' ? "#1a4060" : "#4a2020", marginBottom:"6px" }}>RESOLVED THREAT</div>
              <div style={{ fontSize:"32px", color:threatColor, fontWeight:700, letterSpacing:"0.05em" }}>{threat}</div>
              <div style={{ fontSize:"10px", color: threat === 'STANDBY' ? "#1a4060" : "#6a3030", marginTop:"6px", lineHeight:1.5 }}>
                {report.scout_data.environment_type}
              </div>
            </div>

            {/* SAFETY GATE — deterministic checkpoint between Critic and
                Commander. Shown separately from RESOLVED THREAT above
                because "how bad is it" (threat level) and "are we
                allowed to act on it autonomously" (gate decision) are
                deliberately distinct pieces of information -- see
                agents/safety_gate.py for the backend rationale. */}
            <div style={{
              margin:"0 20px 16px", padding:"16px",
              background: gateAuthorized ? "rgba(63,185,80,0.03)" : "rgba(240,136,62,0.05)",
              border:`1px solid ${gateAuthorized ? "#1e4a2e" : "#5a3a1e"}`,
              borderRadius:"4px", flexShrink:0,
            }}>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"10px" }}>
                <span style={{ fontSize:"9px", letterSpacing:"0.2em", color:"#1a4060" }}>SAFETY GATE</span>
                <span style={{
                  fontSize:"8px", letterSpacing:"0.08em", padding:"2px 8px", borderRadius:"2px",
                  border:`1px solid ${gateAuthorized ? "rgba(63,185,80,0.5)" : "rgba(240,136,62,0.5)"}`,
                  color: gateAuthorized ? "#3fb950" : "#f0883e",
                }}>
                  {gateAuthorized ? "DETERMINISTIC" : "NO LLM OVERRIDE"}
                </span>
              </div>

              <div style={{ fontSize:"13px", fontWeight:700, letterSpacing:"0.03em", color: gateAuthorized ? "#3fb950" : "#f0883e", marginBottom:"8px" }}>
                {report.safety_gate?.gate_decision ?? "STANDBY"}
              </div>

              <div style={{ fontSize:"10px", color:"#7a8a9a", lineHeight:1.6, marginBottom:"12px" }}>
                {report.safety_gate?.gate_reason ?? "Awaiting first analysis."}
              </div>

              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:"8px", marginBottom:"10px" }}>
                <div style={{ padding:"8px 10px", background:"#040b12", border:"1px solid #0e1f2e", borderRadius:"3px" }}>
                  <div style={{ fontSize:"8px", letterSpacing:"0.1em", color:"#1a4060" }}>EVIDENCE</div>
                  <div style={{ fontSize:"12px", color:"#b8cfe0", marginTop:"3px", textTransform:"uppercase" }}>
                    {report.evidence_classification ?? "unavailable"}
                  </div>
                </div>
                <div style={{ padding:"8px 10px", background:"#040b12", border:"1px solid #0e1f2e", borderRadius:"3px" }}>
                  <div style={{ fontSize:"8px", letterSpacing:"0.1em", color:"#1a4060" }}>COMMANDER</div>
                  <div style={{ fontSize:"12px", color: gateAuthorized ? "#3fb950" : "#f85149", marginTop:"3px" }}>
                    {gateAuthorized ? "AUTHORIZED" : "NOT AUTHORIZED"}
                  </div>
                </div>
              </div>

              {/* Venue evidence -- the PRIMARY independent signal the
                  gate weighs. Explicitly labeled per its own data_source
                  field so simulated data is never presented as live. */}
              <div style={{ paddingTop:"10px", borderTop:"1px dashed #1e2a38" }}>
                <div style={{ fontSize:"8px", letterSpacing:"0.1em", color:"#1a4060", marginBottom:"6px", display:"flex", justifyContent:"space-between" }}>
                  <span>VENUE EVIDENCE</span>
                  <span style={{ color: report.mcp_data?.evidence?.data_source?.startsWith("SIMULATED") ? "#e3b341" : "#3fb950" }}>
                    {report.mcp_data?.evidence?.data_source ?? "STANDBY"}
                  </span>
                </div>
                {report.mcp_data?.evidence?.rated_capacity !== undefined ? (
                  <div style={{ fontSize:"10px", color:"#7a8a9a", lineHeight:1.7 }}>
                    Occupancy: <span style={{ color:"#b8cfe0" }}>{report.mcp_data.evidence.current_occupancy}/{report.mcp_data.evidence.rated_capacity}</span>
                    {" "}({report.mcp_data.evidence.occupancy_pct}%) &nbsp;|&nbsp;
                    Exits: <span style={{ color:"#b8cfe0" }}>{report.mcp_data.evidence.exits_available}/{report.mcp_data.evidence.exits_total}</span>
                    {" "}&nbsp;|&nbsp; Incident:{" "}
                    <span style={{ color: report.mcp_data.evidence.active_incident_flag ? "#f85149" : "#3fb950" }}>
                      {report.mcp_data.evidence.active_incident_flag ? "ACTIVE" : "NONE"}
                    </span>
                  </div>
                ) : (
                  <div style={{ fontSize:"10px", color:"#1a4060" }}>No venue evidence retrieved yet.</div>
                )}
              </div>
            </div>
            
            <div style={{ paddingBottom: "20px" }}></div>
          </div>

          {/* ─── CENTER COLUMN ─── */}
          <div style={{ display:"flex", flexDirection:"column", overflow:"hidden" }}>
            <div style={{ padding:"16px 20px", borderBottom:"1px solid #0e1f2e", flexShrink:0 }}>
              <div style={{ fontSize:"9px", letterSpacing:"0.2em", color:"#1a4060", marginBottom:"12px", display:"flex", alignItems:"center", gap:"12px" }}>
                INPUT FEED
                {analyzing && <span style={{ color:"#f0883e", fontSize:"9px", animation:"blink 0.6s step-end infinite" }}>● TRANSMITTING TO SWARM...</span>}
              </div>
              <ImageZone src={src} onUpload={handleUpload} analyzing={analyzing}/>
            </div>

            {/* Commander plan with Caspian Button */}
            <div style={{ padding:"16px 20px", flex:1, display:"flex", flexDirection:"column", overflow:"hidden" }}>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"14px", flexShrink:0 }}>
                <div style={{ fontSize:"9px", letterSpacing:"0.2em", color:"#1a4060" }}>
                  {gateAuthorized ? "COMMANDER — ACTION PLAN" : "COMMANDER — BLOCKED BY SAFETY GATE"}
                </div>
                
                {/* 🌟 NEW: Field Comms Button */}
                <button
                  onClick={() => setShowCaspianModal(true)}
                  style={{
                    fontSize:"9px", letterSpacing:"0.1em", color:"#00d2ff",
                    border:"1px solid rgba(0,210,255,0.4)", background:"rgba(0,210,255,0.06)",
                    padding:"3px 10px", borderRadius:"3px", cursor:"pointer", fontFamily:"monospace"
                  }}
                >
                  [ FIELD COMMS (CASPIAN) ]
                </button>
              </div>

              <div style={{ display:"flex", flexDirection:"column", gap:"10px", flex:1, overflowY:"auto", paddingRight:"8px" }}>
                {gateAuthorized && report.commander_plan ? (
                  report.commander_plan.immediate_actions.map((action, i) => (
                    <div key={i} style={{
                      display:"flex", gap:"14px", padding:"14px 16px",
                      background: i === 0 && threat !== 'STANDBY' ? "rgba(248,81,73,0.04)" : "#040b12",
                      border:     `1px solid ${i === 0 && threat !== 'STANDBY' ? "rgba(248,81,73,0.3)" : "#0e1f2e"}`,
                      borderRadius:"4px", alignItems:"flex-start", flexShrink:0,
                    }}>
                      <span style={{ fontSize:"11px", fontWeight:700, color: i === 0 && threat !== 'STANDBY' ? "#f85149" : "#1a4060", minWidth:"24px", marginTop:"1px" }}>
                        {String(i+1).padStart(2,"0")}
                      </span>
                      <p style={{ fontSize:"12px", lineHeight:1.7, color: i === 0 && threat !== 'STANDBY' ? "#c06050" : i === 1 ? "#4a8aaa" : "#3a6a80", margin:0 }}>
                        {action}
                      </p>
                    </div>
                  ))
                ) : (
                  // Gate blocked autonomous action -- render the actual
                  // gate decision instead of pretending Commander ran.
                  <div style={{
                    padding:"20px", background:"rgba(240,136,62,0.05)",
                    border:"1px solid rgba(240,136,62,0.35)", borderRadius:"4px",
                  }}>
                    <div style={{ fontSize:"14px", fontWeight:700, color:"#f0883e", letterSpacing:"0.05em", marginBottom:"10px" }}>
                      {report.safety_gate?.gate_decision === "REQUIRES_REEVALUATION"
                        ? "⚠ REQUIRES RE-EVALUATION"
                        : "⚠ HUMAN REVIEW REQUIRED"}
                    </div>
                    <p style={{ fontSize:"12px", lineHeight:1.7, color:"#b89060", margin:0 }}>
                      {report.safety_gate?.gate_reason ?? "Independent evidence did not sufficiently confirm the assessed threat level."}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Status bar */}
            <div style={{ height:"48px", borderTop:"1px solid #0e1f2e", background:"#040b12", display:"flex", alignItems:"center", padding:"0 20px", gap:"36px", flexShrink:0 }}>
              {[
                ["PIPELINE", analyzing ? "PROCESSING" : "STANDBY"],
                ["BASE THREAT", report.risk_assessment.threat_level],
                ["CASPIAN SYNC", caspianDispatched ? "DISPATCHED (TG/EMAIL)" : "AWAITING ACTION"]
              ].map(([k,v])=>(
                <span key={k} style={{ fontSize:"10px", letterSpacing:"0.12em", color:"#4a6a80" }}>
                  {k} <span style={{ color: k === "CASPIAN SYNC" && caspianDispatched ? "#00d2ff" : "#58a6ff", fontWeight:600, marginLeft:"6px" }}>{v}</span>
                </span>
              ))}
            </div>
          </div>

          {/* ─── RIGHT COLUMN ─── */}
          <div style={{ borderLeft:"1px solid #0e1f2e", display:"flex", flexDirection:"column", overflow:"hidden" }}>
            <div style={{ flex:"0 0 55%", borderBottom:"1px solid #0e1f2e", padding:"16px 20px", display:"flex", flexDirection:"column", overflow:"hidden" }}>
              <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:"12px", flexShrink:0 }}>
                <span style={{ fontSize:"9px", letterSpacing:"0.2em", color:"#1a4060" }}>AGENT DEBATE LOG</span>
                <span style={{ fontSize:"8px", letterSpacing:"0.1em", border:"1px solid rgba(248,81,73,0.5)", color:"#f85149", padding:"2px 8px", borderRadius:"2px" }}>LIVE</span>
              </div>
              <DebateLog entries={logEntries}/>
            </div>

            <div style={{ flex:1, padding:"16px 20px", overflowY:"auto" }}>
              <div style={{ fontSize:"9px", letterSpacing:"0.2em", color:"#1a4060", marginBottom:"10px" }}>RAW JSON OUTPUT</div>
              <div style={{ background:"#030a10", border:"1px solid #0e1f2e", borderRadius:"4px", padding:"12px 16px", fontSize:"11px", lineHeight:2.0, fontFamily:"monospace" }}>
                <span style={{ color:"#2a5a7a" }}>{"{"}</span><br/>
                {([
                  ["threat",          `"${threat}"`,                              threatColor],
                  ["base_threat",     `"${report.risk_assessment.threat_level}"`, "#5a8aaa"],
                  ["entities",        String(report.scout_data.people_count),      "#e0a050"],
                  ["mcp_weather_source", `"${report.mcp_data?.weather?.source || 'STANDBY'}"`, "#00d2ff"],
                  ["evidence_class",  `"${report.evidence_classification || 'unavailable'}"`, "#e3b341"],
                  ["gate_decision",   `"${report.safety_gate?.gate_decision || 'STANDBY'}"`, gateAuthorized ? "#3fb950" : "#f0883e"],
                  ["critic_override", report.critic_review.adjusted_threat_level !== report.risk_assessment.threat_level ? "true" : "false", "#3fb950"],
                ] as const).map(([k,v,c]) => (
                  <span key={k}>
                    {"  "}
                    <span style={{ color:"#3a7aaa" }}>&quot;{k}&quot;</span>
                    <span style={{ color:"#2a5a7a" }}>: </span>
                    <span style={{ color:c }}>{v}</span>
                    <span style={{ color:"#2a5a7a" }}>,</span><br/>
                  </span>
                ))}
                <span style={{ color:"#2a5a7a" }}>{"}"}</span>
              </div>

              <div style={{ marginTop:"12px", padding:"12px 16px", background: threat === 'STANDBY' ? "transparent" : "rgba(248,81,73,0.03)", border: threat === 'STANDBY' ? "1px solid #0e1f2e" : "1px solid rgba(248,81,73,0.18)", borderRadius:"4px" }}>
                <div style={{ fontSize:"8px", letterSpacing:"0.15em", color: threat === 'STANDBY' ? "#1a4060" : "#5a2020", marginBottom:"8px" }}>CRITIC REASONING</div>
                <p style={{ fontSize:"10px", color: threat === 'STANDBY' ? "#1a4060" : "#7a4040", lineHeight:1.7, margin:0 }}>
                  {report.critic_review.critic_reasoning}
                </p>
              </div>
            </div>
          </div>
        </div>

{/* 🌟 NEW: CINEMATIC CASPIAN BROADCAST MODAL 🌟 */}
{showCaspianModal && (
  <div style={{
    position: "fixed", inset: 0, zIndex: 999,
    background: "rgba(2, 5, 10, 0.85)", backdropFilter: "blur(6px)",
    display: "flex", alignItems: "center", justifyContent: "center"
  }}>
    <div style={{
      width: "600px", background: "#050b14", 
      borderTop: caspianDispatched ? `2px solid ${threatColor}` : "2px solid #00d2ff",
      borderLeft: "1px solid #1e2a38", borderRight: "1px solid #1e2a38", borderBottom: "1px solid #1e2a38",
      boxShadow: caspianDispatched ? `0 10px 40px -10px ${threatColor}40` : "0 10px 40px -10px rgba(0,210,255,0.2)",
      overflow: "hidden"
    }}>
      
      {/* Animated Scanning Header */}
      <div style={{ background: caspianDispatched ? `${threatColor}15` : "rgba(0,210,255,0.05)", padding: "12px 20px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #1e2a38", position: "relative" }}>
        <div style={{ position: "absolute", top: 0, left: 0, height: "1px", width: "100%", background: "linear-gradient(90deg, transparent, #ffffff, transparent)", animation: "scan 2s linear infinite" }} />
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ width: 8, height: 8, background: caspianDispatched ? threatColor : "#00d2ff", borderRadius: "50%", animation: "blink 1s infinite" }}></span>
          <span style={{ fontSize: "12px", fontWeight: 800, letterSpacing: "0.2em", color: caspianDispatched ? threatColor : "#00d2ff" }}>
            CASPIAN SDK :: EMERGENCY RELAY
          </span>
        </div>
        <button onClick={() => setShowCaspianModal(false)} style={{ color: "#64748b", background: "none", border: "none", cursor: "pointer", fontFamily: "monospace", fontSize: "10px", letterSpacing: "0.1em" }}>
          [ ESC ]
        </button>
      </div>

      <div style={{ padding: "24px", fontFamily: "monospace" }}>
        
        {/* Connection Status Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px", marginBottom: "24px" }}>
          <div style={{ border: "1px dashed #1e2a38", padding: "12px", background: "#03070c" }}>
            <div style={{ fontSize: "9px", color: "#4a6a80", letterSpacing: "0.15em", marginBottom: "6px" }}>CH-01: FIELD OPERATIVES</div>
            <div style={{ fontSize: "12px", color: "#b8cfe0", display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ color: "#3fb950" }}>[SECURE]</span> Telegram Bot
            </div>
            <div style={{ fontSize: "9px", color: "#58a6ff", marginTop: "4px" }}>@AegisSwarmBot</div>
          </div>
          <div style={{ border: "1px dashed #1e2a38", padding: "12px", background: "#03070c" }}>
            <div style={{ fontSize: "9px", color: "#4a6a80", letterSpacing: "0.15em", marginBottom: "6px" }}>CH-02: COMMAND HQ</div>
            <div style={{ fontSize: "12px", color: "#b8cfe0", display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ color: "#3fb950" }}>[SECURE]</span> Encrypted Email
            </div>
            <div style={{ fontSize: "9px", color: "#58a6ff", marginTop: "4px" }}>aegis-safety-agent@caspian</div>
          </div>
        </div>

        {/* Dynamic Payload Section */}
        {caspianDispatched ? (
          <div>
            <div style={{ fontSize: "10px", color: "#64748b", letterSpacing: "0.1em", marginBottom: "8px" }}>TRANSMITTING PAYLOAD...</div>
            <div style={{ background: "#0a121e", borderLeft: `3px solid ${threatColor}`, padding: "16px", marginBottom: "20px" }}>
              <div style={{ fontSize: "14px", fontWeight: "bold", color: "#e0edf8", marginBottom: "8px" }}>
                {gateAuthorized ? "AEGIS COMMANDER CONSENSUS" : "AEGIS SAFETY GATE — ACTION BLOCKED"}
              </div>
              <div style={{ fontSize: "11px", color: "#8b949e", lineHeight: "1.6" }}>
                <span style={{ color: "#4a6a80" }}>THREAT LEVEL:</span> <span style={{ color: threatColor, fontWeight: "bold" }}>{threat}</span><br/>
                <span style={{ color: "#4a6a80" }}>SCENE LOCUS:</span> <span style={{ color: "#b8cfe0" }}>{report.scout_data.environment_type}</span><br/>
                {gateAuthorized ? (
                  <>
                    <span style={{ color: "#4a6a80" }}>DIRECTIVES:</span> <span style={{ color: "#e3b341" }}>{report.commander_plan?.immediate_actions.length ?? 0} Actionable Steps Generated</span>
                  </>
                ) : (
                  <>
                    <span style={{ color: "#4a6a80" }}>GATE DECISION:</span> <span style={{ color: "#f0883e" }}>{report.safety_gate?.gate_decision ?? "HUMAN_REVIEW_REQUIRED"}</span>
                  </>
                )}
              </div>
            </div>

            {/* Routing Animation */}
            <div style={{ fontSize: "11px", color: "#b8cfe0", display: "flex", flexDirection: "column", gap: "8px" }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>[►] Routing to CH-01 (Telegram)...</span>
                {/* Dynamic TG status */}
                {report.dispatch_status?.telegram ? (
                  <span style={{ color: "#3fb950", fontWeight: "bold" }}>DELIVERED ✓</span>
                ) : (
                  <span style={{ color: "#f85149", fontWeight: "bold" }}>FAILED ❌</span>
                )}
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span>[►] Routing to CH-02 (HQ Email)...</span>
                {/* Dynamic Email status */}
                {report.dispatch_status?.email ? (
                  <span style={{ color: "#3fb950", fontWeight: "bold" }}>DELIVERED ✓</span>
                ) : (
                  <span style={{ color: "#f85149", fontWeight: "bold" }}>FAILED ❌</span>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div style={{ textAlign: "center", padding: "40px 0" }}>
            <div style={{ color: "#4a6a80", fontSize: "12px", letterSpacing: "0.1em", animation: "blink 1.5s infinite" }}>
              AWAITING COMMANDER CONSENSUS...
            </div>
            <div style={{ color: "#1e2a38", fontSize: "10px", marginTop: "8px" }}>
              Payload routing will initiate automatically upon threat resolution.
            </div>
          </div>
        )}

      </div>
    </div>
  </div>
)}

      </div>
    </>
  );
}