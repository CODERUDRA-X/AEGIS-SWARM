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

interface ReportData {
  scout_data: {
    people_count:     number;
    blocked_paths:    number;
    environment_type: string;
    hazard_factors:   string[];
  };
  mcp_data?: {
    source: string;
    temperature: string;
    wind_speed: string;
    mcp_status: string;
  };
  risk_assessment:  { threat_level: string };
  critic_review:    { adjusted_threat_level: string; critic_reasoning: string };
  commander_plan:   { immediate_actions: string[] };
}

/* ── Constants ───────────────────────────────────────────────────────── */

const AGENT_STYLES: Record<AgentName, { border: string; text: string; bg: string }> = {
  SCOUT:  { border: "#58a6ff", text: "#58a6ff", bg: "rgba(88,166,255,0.09)"   },
  MCP:    { border: "#00d2ff", text: "#00d2ff", bg: "rgba(0,210,255,0.09)"    }, // New MCP Agent Style
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
    source: "OFFLINE",
    temperature: "--",
    wind_speed: "--",
    mcp_status: "Standby",
  },
  risk_assessment:  { threat_level: "STANDBY" },
  critic_review: {
    adjusted_threat_level: "STANDBY",
    critic_reasoning: "System idle. Awaiting visual telemetry to initiate swarm pipeline.",
  },
  commander_plan: {
    immediate_actions: [
      "Upload aerial or CCTV feed to initialize.",
      "Standby for agent routing...",
      "Maintain perimeter.",
    ],
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
      fontSize:       "8px",
      fontWeight:     600,
      letterSpacing:  "0.08em",
      border:         `1px solid ${s.border}`,
      color:          s.text,
      background:     s.bg,
      borderRadius:   "2px",
      height:         "18px",
      minWidth:       "42px",
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
    <div ref={ref} style={{ flex:1, overflowY:"auto", paddingRight:"4px", fontSize:"10px" }}>
      {entries.filter(Boolean).map((entry, i) => (
        <div key={i} style={{ display:"grid", gridTemplateColumns:"52px 46px 1fr", gap:"2px", marginBottom:"10px", animation:"logIn 0.25s ease" }}>
          <span style={{ color:"#1e3a52", paddingTop:"2px", fontFamily:"monospace" }}>{entry.ts}</span>
          <AgentBadge agent={entry.agent} />
          <span style={{ lineHeight:1.6, color:msgColor(entry.highlight), fontWeight: entry.highlight==="override" ? 600 : 400 }}>
            {entry.msg}
          </span>
        </div>
      ))}

      {/* blinking cursor line */}
      <div style={{ display:"flex", alignItems:"center", gap:"8px", marginTop:"6px", paddingTop:"6px", borderTop:"1px solid #0e1f2e" }}>
        <span style={{ display:"inline-block", width:6, height:12, background:"#1e4a6a", animation:"blink 1s step-end infinite" }} />
        <span style={{ fontSize:"8px", letterSpacing:"0.12em", color:"#1a3a52" }}>PIPELINE ACTIVE</span>
      </div>
    </div>
  );
}

/* ── SwarmTopology ───────────────────────────────────────────────────── */

function SwarmTopology({ activeAgent }: { activeAgent: string | null }) {
  return (
    <svg viewBox="0 0 260 210" xmlns="http://www.w3.org/2000/svg" style={{ width:"100%", height:"100%" }}>
      <defs>
        <marker id="a1" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
          <path d="M2 1L8 5L2 9" fill="none" stroke="#1e4a6a" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </marker>
        <marker id="a2" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
          <path d="M2 1L8 5L2 9" fill="none" stroke="#f85149" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </marker>
      </defs>

      {/* flow lines */}
      <line x1="130" y1="38" x2="52"  y2="98"  stroke="#1e4a6a" strokeWidth="1" markerEnd="url(#a1)"/>
      <line x1="130" y1="38" x2="208" y2="98"  stroke="#1e4a6a" strokeWidth="1" markerEnd="url(#a1)"/>
      <line x1="52"  y1="118" x2="125" y2="170" stroke="#0e2030" strokeWidth="0.5" strokeDasharray="4 3"/>
      <line x1="208" y1="118" x2="135" y2="170" stroke="#0e2030" strokeWidth="0.5" strokeDasharray="4 3"/>

      {/* animated debate edge */}
      <line x1="72" y1="108" x2="188" y2="108"
        stroke="#f85149" strokeWidth="1.5" opacity={activeAgent === 'CRITIC' ? 0.9 : 0.3}
        strokeDasharray="6 4"
        markerEnd="url(#a2)" markerStart="url(#a2)"
        style={activeAgent === 'CRITIC' ? { animation:"debateDash 1s linear infinite" } : {}}
      />
      <text x="130" y="103" fill={activeAgent === 'CRITIC' ? "#f85149" : "#7a2020"} fontSize="7" textAnchor="middle" letterSpacing="2" fontFamily="monospace">DEBATE</text>

      {/* SCOUT */}
      <rect x="90" y="14" width="80" height="32" rx="3" fill="rgba(88,166,255,0.06)" stroke={activeAgent === 'SCOUT' ? "#ffffff" : "#58a6ff"} strokeWidth={activeAgent === 'SCOUT' ? "1.5" : "0.7"}/>
      <text x="130" y="27" textAnchor="middle" fill="#58a6ff" fontSize="9" fontWeight="500" letterSpacing="1.5" fontFamily="monospace">SCOUT</text>
      <text x="130" y="40" textAnchor="middle" fill="#2a6a8a" fontSize="7" letterSpacing="1" fontFamily="monospace">{activeAgent ? 'ACTIVE ●' : 'DONE ✓'}</text>

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
      <rect x="90" y="162" width="80" height="32" rx="3" fill="#060f1a" stroke={activeAgent === 'CMD' ? "#a371f7" : "#1e2a38"} strokeWidth="0.5"/>
      <text x="130" y="175" textAnchor="middle" fill={activeAgent === 'CMD' ? "#a371f7" : "#2a3a4a"} fontSize="9" letterSpacing="1.5" fontFamily="monospace">COMMAND</text>
      <text x="130" y="188" textAnchor="middle" fill="#1a2a3a" fontSize="7" letterSpacing="1" fontFamily="monospace">PENDING…</text>
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
        height:       "220px",
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
      {/* grid overlay */}
      <div style={{
        position:"absolute", inset:0, pointerEvents:"none",
        backgroundImage:"linear-gradient(rgba(30,80,120,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(30,80,120,.05) 1px,transparent 1px)",
        backgroundSize:"28px 28px",
      }}/>

      {/* corner reticles */}
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

      {/* scan line while analyzing */}
      {analyzing && <div style={{
        position:"absolute", left:0, right:0, height:"1px",
        background:"linear-gradient(90deg,transparent,rgba(88,166,255,0.4),transparent)",
        animation:"scan 2s linear infinite",
      }}/>}

      {src
        ? <img src={src} alt="feed" style={{ position:"absolute", inset:0, width:"100%", height:"100%", objectFit:"contain" }}/>
        : (
          <div style={{ position:"absolute", inset:0, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", gap:"8px" }}>
            <svg style={{ width:28, height:28, color:"#1e4a6a" }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/>
            </svg>
            <span style={{ fontSize:"9px", letterSpacing:"0.2em", color:"#1e4a6a" }}>
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
  
  // Real dynamic report state
  const [report, setReport]   = useState<ReportData>(INITIAL_REPORT);
  const [activeAgent, setActiveAgent] = useState<string | null>(null);

  /* frame counter */
  useEffect(() => {
    const id = setInterval(() => setFrame(f => f + 1), 900);
    return () => clearInterval(id);
  }, []);

  const getLogTimestamp = () => {
    const d = new Date();
    return `${String(d.getUTCHours()).padStart(2,"0")}:${String(d.getUTCMinutes()).padStart(2,"0")}:${String(d.getUTCSeconds()).padStart(2,"0")}`;
  };

  // REAL API UPLOAD LOGIC
  const handleUpload = useCallback(async (file: File) => {
    setSrc(URL.createObjectURL(file));
    setAn(true);
    setReport(INITIAL_REPORT);
    setLog([]);
    setActiveAgent('SCOUT');

    setLog([{ ts: getLogTimestamp(), agent: "SCOUT", highlight: "normal", msg: `Uplink established. Analyzing: ${file.name}...` }]);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/api/analyze", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      
      if (data.error) throw new Error(data.error);
      
      setReport(data as ReportData);

      // Create a dynamic sequence of logs based on the real data
      const dynamicLogs: LogEntry[] = [
        { ts: getLogTimestamp(), agent: "SCOUT", highlight: "normal", msg: `Extraction complete. Terrain: ${data.scout_data.environment_type}. Detected ${data.scout_data.people_count} entities.` },
        { ts: getLogTimestamp(), agent: "MCP", highlight: "mcp", msg: `Tool Invoked: Live Telemetry. Temp: ${data.mcp_data?.temperature}, Wind: ${data.mcp_data?.wind_speed}.` },
        { ts: getLogTimestamp(), agent: "RISK", highlight: "normal", msg: `Base threat evaluated: ${data.risk_assessment.threat_level}.` }
      ];

      if (data.critic_review.adjusted_threat_level !== data.risk_assessment.threat_level) {
        dynamicLogs.push({ ts: getLogTimestamp(), agent: "CRITIC", highlight: "warn", msg: "Challenging baseline assumption using MCP & Visual data." });
        dynamicLogs.push({ ts: getLogTimestamp(), agent: "CRITIC", highlight: "override", msg: `OVERRIDE: ${data.risk_assessment.threat_level} → ${data.critic_review.adjusted_threat_level}.` });
      } else {
        dynamicLogs.push({ ts: getLogTimestamp(), agent: "CRITIC", highlight: "normal", msg: `Concur with Risk Assessment: ${data.risk_assessment.threat_level}.` });
      }

      dynamicLogs.push({ ts: getLogTimestamp(), agent: "CMD", highlight: "cmd", msg: "Consensus received. Executing 3-step action plan." });

      let i = 0;
      const logInterval = setInterval(() => {
        if (i < dynamicLogs.length) {
          const currentLog = dynamicLogs[i];
          setLog(prev => [...prev, currentLog]);
          setActiveAgent(currentLog.agent === "MCP" ? "SCOUT" : currentLog.agent); // Keep scout active during MCP
          i++;
        } else {
          clearInterval(logInterval);
          setActiveAgent(null);
          setAn(false);
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

  return (
    <>
      {/* ── keyframes injected once ── */}
      <style>{`
        @keyframes blink      { 0%,100%{opacity:1} 50%{opacity:0} }
        @keyframes logIn      { from{opacity:0;transform:translateY(3px)} to{opacity:1;transform:none} }
        @keyframes scan       { from{top:0%} to{top:100%} }
        @keyframes debateDash { to{stroke-dashoffset:-20} }
        @keyframes criticGlow { 0%,100%{box-shadow:0 0 8px rgba(248,81,73,.15)} 50%{box-shadow:0 0 22px rgba(248,81,73,.35)} }
        ::-webkit-scrollbar       { width:3px; height:3px }
        ::-webkit-scrollbar-track { background:transparent }
        ::-webkit-scrollbar-thumb { background:#1e2a38; border-radius:2px }
      `}</style>

      <div style={{ height:"100vh", background:"#050c14", color:"#b8cfe0", fontFamily:"'Geist Mono',ui-monospace,monospace", fontSize:"12px", display:"flex", flexDirection:"column", overflow:"hidden" }}>

        {/* ── TOPBAR ── */}
        <header style={{ height:"40px", flexShrink:0, background:"#040b12", borderBottom:"1px solid #0e1f2e", display:"flex", alignItems:"center", padding:"0 20px", gap:"14px" }}>
          <span style={{ fontSize:"13px", fontWeight:600, letterSpacing:"0.22em", color:"#e0edf8" }}>AEGIS–SWARM</span>
          <div style={{ width:"1px", height:"16px", background:"#0e1f2e" }}/>
          <span style={{ fontSize:"9px", display:"flex", alignItems:"center", gap:"5px", letterSpacing:"0.1em", color:"#3fb950" }}>
            <span style={{ width:5, height:5, borderRadius:"50%", background:"#3fb950", display:"inline-block", animation:"blink 1s step-end infinite" }}/>
            LIVE ANALYSIS
          </span>
          <div style={{ marginLeft:"auto", display:"flex", gap:"20px", alignItems:"center" }}>
            <span style={{ fontSize:"9px", letterSpacing:"0.12em", color:"#1a4060" }}>NEURAL MESH / 4-AGENT PIPELINE</span>
            <span style={{ fontSize:"9px", color:"#1a3a52", fontFamily:"monospace" }}>
              FRAME <span style={{ color:"#1e4a6a" }}>{String(frame).padStart(4,"0")}</span>
            </span>
            <span style={{ fontSize:"9px", color:"#1a3052", fontFamily:"monospace" }}>{utcTime}</span>
          </div>
        </header>

        {/* ── MAIN GRID ── */}
        <div style={{ flex:1, display:"grid", gridTemplateColumns:"238px 1fr 278px", overflow:"hidden" }}>

          {/* ─── LEFT COLUMN ─── */}
          <div style={{ borderRight:"1px solid #0e1f2e", display:"flex", flexDirection:"column", overflow:"hidden", overflowY:"auto" }}>

            {/* Topology */}
            <div style={{ padding:"12px 14px", borderBottom:"1px solid #0e1f2e", flexShrink:0 }}>
              <div style={{ fontSize:"8px", letterSpacing:"0.18em", color:"#1a4060", marginBottom:"10px" }}>SWARM TOPOLOGY</div>
              <div style={{ height:"208px" }}>
                <SwarmTopology activeAgent={activeAgent}/>
              </div>
            </div>

            {/* MCP TELEMETRY (NEW PANEL) */}
            <div style={{ padding:"10px 14px", borderBottom:"1px solid #0e1f2e", flexShrink:0, background: threat === 'STANDBY' ? "transparent" : "rgba(0, 210, 255, 0.02)" }}>
              <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:"8px" }}>
                <span style={{ fontSize:"8px", letterSpacing:"0.18em", color:"#1a4060" }}>MCP TELEMETRY</span>
                <span style={{ fontSize:"7px", letterSpacing:"0.1em", border:"1px solid rgba(0, 210, 255, 0.4)", color:"#00d2ff", padding:"1px 6px", borderRadius:"2px" }}>EXTERNAL API</span>
              </div>
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:"5px", marginBottom:"5px" }}>
                <div style={{ padding:"7px 9px", background:"#040b12", border:"1px solid #0e1f2e", borderRadius:"3px" }}>
                  <div style={{ fontSize:"7px", letterSpacing:"0.12em", color:"#1a4060" }}>WIND SPEED</div>
                  <div style={{ fontSize:"13px", color:"#00d2ff", marginTop:"2px" }}>{report.mcp_data?.wind_speed}</div>
                </div>
                <div style={{ padding:"7px 9px", background:"#040b12", border:"1px solid #0e1f2e", borderRadius:"3px" }}>
                  <div style={{ fontSize:"7px", letterSpacing:"0.12em", color:"#1a4060" }}>TEMPERATURE</div>
                  <div style={{ fontSize:"13px", color:"#00d2ff", marginTop:"2px" }}>{report.mcp_data?.temperature}</div>
                </div>
              </div>
              <div style={{ fontSize:"7px", color:"#4a6a80", letterSpacing:"0.05em", textTransform: 'uppercase' }}>
                SRC: {report.mcp_data?.source}
              </div>
            </div>

            {/* Scout data */}
            <div style={{ padding:"10px 14px", borderBottom:"1px solid #0e1f2e", flexShrink:0 }}>
              <div style={{ fontSize:"8px", letterSpacing:"0.18em", color:"#1a4060", marginBottom:"8px" }}>SCOUT EXTRACTION</div>
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:"5px" }}>
                {[
                  { k:"ENTITIES",  v:String(report.scout_data.people_count),  c:"#b8cfe0" },
                  { k:"PATHS OUT", v:String(report.scout_data.blocked_paths), c:"#f0883e" },
                  { k:"TERRAIN",   v:report.scout_data.environment_type.split(' ')[0], c:"#58a6ff" },
                  { k:"HAZARDS",   v:String(report.scout_data.hazard_factors.length), c:"#f85149" },
                ].map(({ k, v, c }) => (
                  <div key={k} style={{ padding:"7px 9px", background:"#040b12", border:"1px solid #0e1f2e", borderRadius:"3px" }}>
                    <div style={{ fontSize:"7px", letterSpacing:"0.12em", color:"#1a4060" }}>{k}</div>
                    <div style={{ fontSize:"15px", color:c, marginTop:"2px", textTransform: 'capitalize' }}>{v}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Threat display */}
            <div style={{ margin:"10px 14px", padding:"12px", background: threat === 'STANDBY' ? "#03070c" : "rgba(248,81,73,0.04)", border:`1px solid ${threatColor}`, borderRadius:"4px", flexShrink:0, animation: threat !== 'STANDBY' ? "criticGlow 2.5s ease-in-out infinite" : "none" }}>
              <div style={{ fontSize:"8px", letterSpacing:"0.14em", color: threat === 'STANDBY' ? "#1a4060" : "#4a2020", marginBottom:"4px" }}>RESOLVED THREAT</div>
              <div style={{ fontSize:"26px", color:threatColor, fontWeight:600, letterSpacing:"0.04em" }}>{threat}</div>
              <div style={{ fontSize:"9px", color: threat === 'STANDBY' ? "#1a4060" : "#6a3030", marginTop:"4px", lineHeight:1.5 }}>
                {report.scout_data.environment_type}
              </div>
            </div>
            
            <div style={{ paddingBottom: "20px" }}></div>
          </div>

          {/* ─── CENTER COLUMN ─── */}
          <div style={{ display:"flex", flexDirection:"column", overflow:"hidden" }}>

            {/* Image feed */}
            <div style={{ padding:"12px 14px", borderBottom:"1px solid #0e1f2e", flexShrink:0 }}>
              <div style={{ fontSize:"8px", letterSpacing:"0.18em", color:"#1a4060", marginBottom:"8px", display:"flex", alignItems:"center", gap:"12px" }}>
                INPUT FEED
                {analyzing && <span style={{ color:"#f0883e", fontSize:"8px", animation:"blink 0.6s step-end infinite" }}>● TRANSMITTING TO SWARM...</span>}
              </div>
              <ImageZone src={src} onUpload={handleUpload} analyzing={analyzing}/>
            </div>

            {/* Commander plan */}
            <div style={{ padding:"12px 14px", flex:1, display:"flex", flexDirection:"column", overflow:"hidden" }}>
              <div style={{ fontSize:"8px", letterSpacing:"0.18em", color:"#1a4060", marginBottom:"10px", flexShrink:0 }}>COMMANDER — 3-STEP PLAN</div>
              <div style={{ display:"flex", flexDirection:"column", gap:"7px", flex:1, overflowY:"auto" }}>
                {report.commander_plan.immediate_actions.map((action, i) => (
                  <div key={i} style={{
                    display:"flex", gap:"12px", padding:"10px 12px",
                    background: i === 0 && threat !== 'STANDBY' ? "rgba(248,81,73,0.04)" : "#040b12",
                    border:     `1px solid ${i === 0 && threat !== 'STANDBY' ? "rgba(248,81,73,0.3)" : "#0e1f2e"}`,
                    borderRadius:"3px", alignItems:"flex-start", flexShrink:0,
                  }}>
                    <span style={{ fontSize:"9px", fontWeight:600, color: i === 0 && threat !== 'STANDBY' ? "#f85149" : "#1a4060", minWidth:"20px", marginTop:"1px" }}>
                      {String(i+1).padStart(2,"0")}
                    </span>
                    <p style={{ fontSize:"11px", lineHeight:1.6, color: i === 0 && threat !== 'STANDBY' ? "#c06050" : i === 1 ? "#4a8aaa" : "#3a6a80", margin:0 }}>
                      {action}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Status bar */}
            <div style={{ height:"32px", borderTop:"1px solid #0e1f2e", background:"#040b12", display:"flex", alignItems:"center", padding:"0 14px", gap:"22px", flexShrink:0 }}>
              {[["PIPELINE", analyzing ? "PROCESSING" : "STANDBY"],["BASE THREAT", report.risk_assessment.threat_level]].map(([k,v])=>(
                <span key={k} style={{ fontSize:"8px", letterSpacing:"0.08em", color:"#1a3a52" }}>
                  {k} <span style={{ color:"#1e5a7a" }}>{v}</span>
                </span>
              ))}
            </div>
          </div>

          {/* ─── RIGHT COLUMN ─── */}
          <div style={{ borderLeft:"1px solid #0e1f2e", display:"flex", flexDirection:"column", overflow:"hidden" }}>

            {/* Debate log */}
            <div style={{ flex:"0 0 55%", borderBottom:"1px solid #0e1f2e", padding:"12px 14px", display:"flex", flexDirection:"column", overflow:"hidden" }}>
              <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:"10px", flexShrink:0 }}>
                <span style={{ fontSize:"8px", letterSpacing:"0.18em", color:"#1a4060" }}>AGENT DEBATE LOG</span>
                <span style={{ fontSize:"7px", letterSpacing:"0.1em", border:"1px solid rgba(248,81,73,0.5)", color:"#f85149", padding:"1px 6px", borderRadius:"2px" }}>LIVE</span>
              </div>
              <DebateLog entries={logEntries}/>
            </div>

            {/* JSON output */}
            <div style={{ flex:1, padding:"12px 14px", overflowY:"auto" }}>
              <div style={{ fontSize:"8px", letterSpacing:"0.18em", color:"#1a4060", marginBottom:"8px" }}>RAW JSON OUTPUT</div>
              <div style={{ background:"#030a10", border:"1px solid #0e1f2e", borderRadius:"3px", padding:"10px 12px", fontSize:"10px", lineHeight:1.9, fontFamily:"monospace" }}>
                <span style={{ color:"#2a5a7a" }}>{"{"}</span><br/>
                {([
                  ["threat",          `"${threat}"`,                              threatColor],
                  ["base_threat",     `"${report.risk_assessment.threat_level}"`, "#5a8aaa"],
                  ["entities",        String(report.scout_data.people_count),      "#e0a050"],
                  ["mcp_source",      `"${report.mcp_data?.source || 'STANDBY'}"`, "#00d2ff"],
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

              {/* Critic reasoning */}
              <div style={{ marginTop:"8px", padding:"9px 12px", background: threat === 'STANDBY' ? "transparent" : "rgba(248,81,73,0.03)", border: threat === 'STANDBY' ? "1px solid #0e1f2e" : "1px solid rgba(248,81,73,0.18)", borderRadius:"3px" }}>
                <div style={{ fontSize:"7px", letterSpacing:"0.14em", color: threat === 'STANDBY' ? "#1a4060" : "#5a2020", marginBottom:"5px" }}>CRITIC REASONING</div>
                <p style={{ fontSize:"9px", color: threat === 'STANDBY' ? "#1a4060" : "#7a4040", lineHeight:1.6, margin:0 }}>
                  {report.critic_review.critic_reasoning}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}