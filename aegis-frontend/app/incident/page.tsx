'use client';

// ================================================================
// AEGIS-SWARM :: Incident Deep-Link Page
// ================================================================
// WHY THIS FILE EXISTS:
// Dispatched alerts previously linked to the generic homepage, which
// showed nothing specific to the incident that triggered the alert --
// a responder clicking the link saw a blank "upload an image" screen,
// not the decision that was just made. This page fixes that WITHOUT
// needing a database: the backend encodes a compact summary of the
// incident directly into the URL (see build_incident_link() in
// server.py), and this page decodes it client-side and renders it.
//
// Route: /incident?d=<base64-encoded-json>
// ================================================================

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';

interface IncidentData {
  scene?: string;
  threat?: string;
  reasoning?: string;
  evidence_classification?: string;
  gate_decision?: string;
  actions?: string[];
}

const THREAT_COLORS: Record<string, string> = {
  CRITICAL: '#E53935',
  HIGH: '#F0883E',
  MEDIUM: '#F0C419',
  LOW: '#2EA043',
};

// Matches the palette/terminology already used on the main dashboard
// (page.tsx) so a responder who has seen both never gets conflicting
// signals about the same decision.
const GATE_STYLES: Record<string, { label: string; color: string }> = {
  AUTONOMOUS_ACTION_AUTHORIZED: { label: 'AUTHORIZED', color: '#3FB950' },
  HUMAN_REVIEW_REQUIRED:        { label: 'HUMAN REVIEW REQUIRED', color: '#F0883E' },
  REQUIRES_REEVALUATION:        { label: 'REQUIRES RE-EVALUATION', color: '#F0883E' },
};

function IncidentContent() {
  const searchParams = useSearchParams();
  const encoded = searchParams.get('d');

  let incident: IncidentData | null = null;
  let decodeFailed = false;

  if (encoded) {
    try {
      const json = decodeURIComponent(escape(atob(encoded)));
      incident = JSON.parse(json);
    } catch {
      decodeFailed = true;
    }
  }

  if (!encoded || decodeFailed || !incident) {
    return (
      <div style={styles.page}>
        <div style={styles.container}>
          <p style={{ color: '#8B949E', fontSize: 14 }}>
            No incident data found in this link.
          </p>
          <a href="/" style={styles.ctaButton}>
            Open Live Dashboard &rarr;
          </a>
        </div>
      </div>
    );
  }

  const threatColor = THREAT_COLORS[incident.threat ?? ''] ?? '#8B949E';
  // Older alerts (sent before the safety gate existed) won't have
  // gate_decision in their encoded payload -- default to authorized so
  // those historical links still render their action plan as before.
  const gateInfo = incident.gate_decision
    ? GATE_STYLES[incident.gate_decision] ?? { label: incident.gate_decision, color: '#8B949E' }
    : null;
  const gateAuthorized = incident.gate_decision
    ? incident.gate_decision === 'AUTONOMOUS_ACTION_AUTHORIZED'
    : true;

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        <div style={styles.header}>
          <h1 style={styles.brand}>AEGIS&#8209;SWARM</h1>
          <p style={styles.brandSub}>Consensus Incident Report</p>
        </div>

        <p style={styles.label}>Threat Level</p>
        <p style={{ ...styles.threatValue, color: threatColor }}>
          {incident.threat}
        </p>

        {gateInfo && (
          <>
            <p style={styles.label}>Safety Gate Decision</p>
            <p style={{ ...styles.value, color: gateInfo.color, fontWeight: 700 }}>
              {gateInfo.label}
            </p>
          </>
        )}

        {incident.evidence_classification && (
          <>
            <p style={styles.label}>Evidence Classification</p>
            <p style={styles.value}>{incident.evidence_classification}</p>
          </>
        )}

        <p style={styles.label}>Scene</p>
        <p style={styles.value}>{incident.scene}</p>

        <p style={styles.label}>Critic Reasoning</p>
        <p style={styles.reasoning}>{incident.reasoning}</p>

        <p style={styles.label}>
          {gateAuthorized ? 'Commander Action Plan' : 'Action Plan — Blocked by Safety Gate'}
        </p>
        {gateAuthorized ? (
          <ol style={styles.actionsList}>
            {(incident.actions ?? []).map((action, i) => (
              <li key={i} style={styles.actionItem}>
                {action}
              </li>
            ))}
          </ol>
        ) : (
          <p style={{ ...styles.reasoning, color: '#F0883E' }}>
            No autonomous action plan was generated. This incident requires human review
            before any response is executed.
          </p>
        )}

        <a href="/" style={styles.ctaButton}>
          Open Live Dashboard &rarr;
        </a>
      </div>
    </div>
  );
}

export default function IncidentPage() {
  return (
    <Suspense fallback={<div style={styles.page} />}>
      <IncidentContent />
    </Suspense>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: '100vh',
    background: '#0D1117',
    color: '#F5F7FA',
    fontFamily: '-apple-system, "Segoe UI", sans-serif',
    padding: '48px 20px',
  },
  container: {
    maxWidth: 640,
    margin: '0 auto',
  },
  header: {
    borderBottom: '1px solid #30363D',
    paddingBottom: 16,
    marginBottom: 28,
  },
  brand: {
    margin: 0,
    fontSize: 20,
    letterSpacing: 1,
  },
  brandSub: {
    margin: '4px 0 0',
    color: '#8B949E',
    fontSize: 13,
  },
  label: {
    margin: '0 0 4px',
    color: '#8B949E',
    fontSize: 11,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  threatValue: {
    margin: '0 0 24px',
    fontSize: 30,
    fontWeight: 700,
  },
  value: {
    margin: '0 0 24px',
    fontSize: 15,
  },
  reasoning: {
    margin: '0 0 24px',
    fontSize: 13,
    lineHeight: 1.6,
    color: '#C9D1D9',
  },
  actionsList: {
    margin: '0 0 32px',
    paddingLeft: 20,
    fontSize: 13,
    lineHeight: 1.9,
  },
  actionItem: {
    marginBottom: 4,
  },
  ctaButton: {
    display: 'inline-block',
    background: '#00E5FF',
    color: '#0D1117',
    padding: '10px 22px',
    borderRadius: 6,
    textDecoration: 'none',
    fontSize: 13,
    fontWeight: 700,
  },
};