"""ClaimGuard AI — Sentinel-Ops SOE Demo"""
import os
import time
import streamlit as st
from dotenv import load_dotenv

from claims_agent.soe_client import SOEClient
from claims_agent.agent import process_claim, AGENT_ID

load_dotenv()

st.set_page_config(
    page_title="ClaimGuard AI — SOE Demo",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .main-header { font-size: 2rem; font-weight: 700; color: #1e3a5f; margin-bottom: 0; }
  .sub-header  { color: #64748b; font-size: 0.95rem; margin-bottom: 1.5rem; }
  .step-card   { border-radius: 8px; padding: 12px 16px; margin: 6px 0; border-left: 4px solid #ccc; }
  .step-allow  { background: #f0fdf4; border-color: #22c55e; }
  .step-deny   { background: #fef2f2; border-color: #ef4444; }
  .step-audit  { background: #fffbeb; border-color: #f59e0b; }
  .badge-allow { background: #22c55e; color: white; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 700; }
  .badge-deny  { background: #ef4444; color: white; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 700; }
  .badge-audit { background: #f59e0b; color: white; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 700; }
  .metric-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; text-align: center; }
  .metric-num  { font-size: 2rem; font-weight: 700; }
  .metric-lbl  { color: #64748b; font-size: 0.8rem; }
  .scenario-card { border: 2px solid #e2e8f0; border-radius: 10px; padding: 16px; cursor: pointer; }
  .final-summary { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 16px; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.shields.io/badge/Sentinel--Ops-SOE%20Demo-1e3a5f?style=for-the-badge", use_container_width=True)
    st.markdown("---")

    st.subheader("⚙️ Connection")
    soe_url = st.text_input("SOE API URL", value=os.getenv("SOE_API_URL", ""))
    soe_key = st.text_input("SOE API Key", type="password", value=os.getenv("SOE_API_KEY", ""))
    dashboard_url = os.getenv("SOE_DASHBOARD_URL", soe_url.rstrip("/") + "/dashboard" if soe_url else "")

    soe = SOEClient(api_url=soe_url, api_key=soe_key)

    if st.button("🔌 Test Connection"):
        if soe.health():
            st.success("Connected ✓")
        else:
            st.error("Cannot reach SOE API")

    st.markdown("---")
    if dashboard_url:
        st.markdown(f"[📊 Open SOE Dashboard →]({dashboard_url})")
    st.markdown("---")
    st.caption("**Agent ID:** `claims-processor`")
    st.caption("**Model:** claude-haiku-4-5")
    st.caption("**Mode:** Audit (enforce coming soon)")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-header">🛡️ ClaimGuard AI</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Insurance Claims Processing · Protected by Sentinel-Ops Safe Operating Envelope</div>', unsafe_allow_html=True)

# ── Scenario Selection ────────────────────────────────────────────────────────
st.markdown("### Select a Claim Scenario")

SCENARIOS = {
    "✅ Straightforward Approval": {
        "claim_id": "CLM-2024-001",
        "scenario": "normal",
        "description": "Auto accident claim. Agent reads claim + policy, runs fraud check, writes decision. All actions within SOE.",
        "color": "#22c55e",
    },
    "🔒 PII Protection": {
        "claim_id": "CLM-2024-002",
        "scenario": "pii_attempt",
        "description": "Medical claim. Agent attempts to access raw SSN/PII files — SOE blocks them. Claim processed using only approved data paths.",
        "color": "#f59e0b",
    },
    "🚨 Rogue Behavior Blocked": {
        "claim_id": "CLM-2024-003",
        "scenario": "rogue_behavior",
        "description": "Suspicious large claim. Agent attempts to DELETE audit logs and steal DB credentials — all blocked by SOE.",
        "color": "#ef4444",
    },
}

cols = st.columns(3)
selected = st.session_state.get("selected_scenario", list(SCENARIOS.keys())[0])

for i, (name, info) in enumerate(SCENARIOS.items()):
    with cols[i]:
        border = "3px solid " + info["color"] if name == selected else "2px solid #e2e8f0"
        st.markdown(f"""
        <div style="border:{border};border-radius:10px;padding:16px;min-height:120px">
          <div style="font-weight:700;font-size:1rem">{name}</div>
          <div style="color:#64748b;font-size:0.82rem;margin-top:6px">{info['description']}</div>
          <div style="margin-top:8px;font-family:monospace;font-size:11px;color:#94a3b8">Claim: {info['claim_id']}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Select", key=f"sel_{i}", use_container_width=True):
            st.session_state["selected_scenario"] = name
            st.rerun()

st.markdown("---")

# ── Run Button + Processing ───────────────────────────────────────────────────
scenario_info = SCENARIOS[selected]
col_run, col_spacer = st.columns([1, 3])
with col_run:
    run = st.button("▶ Process Claim", type="primary", use_container_width=True)

if run:
    if not soe_url or not soe_key:
        st.error("Set SOE API URL and API Key in the sidebar first.")
        st.stop()

    soe = SOEClient(api_url=soe_url, api_key=soe_key)

    st.markdown(f"### Processing `{scenario_info['claim_id']}`")

    col_steps, col_metrics = st.columns([3, 1])

    with col_metrics:
        st.markdown("#### Live SOE Stats")
        allow_ph = st.empty()
        deny_ph = st.empty()
        escalate_ph = st.empty()

    with col_steps:
        st.markdown("#### Agent Steps")
        steps_container = st.container()

    allow_count = deny_count = escalate_count = 0
    steps = []

    def render_metrics():
        with allow_ph:
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-num" style="color:#22c55e">{allow_count}</div>
              <div class="metric-lbl">ALLOWED</div>
            </div>""", unsafe_allow_html=True)
        with deny_ph:
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-num" style="color:#ef4444">{deny_count}</div>
              <div class="metric-lbl">DENIED</div>
            </div>""", unsafe_allow_html=True)
        with escalate_ph:
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-num" style="color:#f59e0b">{escalate_count}</div>
              <div class="metric-lbl">AUDIT OVERRIDE</div>
            </div>""", unsafe_allow_html=True)

    render_metrics()

    steps_html_ph = steps_container.empty()

    def render_steps():
        html = ""
        for s in steps:
            if s["enforcement"] == "allow" and not s["audit"]:
                css, badge = "step-allow", '<span class="badge-allow">✓ ALLOW</span>'
            elif s["enforcement"] == "deny":
                css, badge = "step-deny", '<span class="badge-deny">✗ DENY</span>'
            else:
                css, badge = "step-audit", '<span class="badge-audit">⚠ AUDIT</span>'

            audit_tag = ' <span class="badge-audit">AUDIT OVERRIDE</span>' if s["audit"] else ""
            html += f"""
            <div class="step-card {css}">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <div style="font-family:monospace;font-size:13px;font-weight:600">{s['label']}</div>
                <div>{badge}{audit_tag} <span style="color:#94a3b8;font-size:11px">{s['latency']}ms</span></div>
              </div>
              <div style="color:#64748b;font-size:12px;margin-top:4px">{s['reason']}</div>
            </div>"""
        steps_html_ph.markdown(html, unsafe_allow_html=True)

    final_ph = st.empty()

    with st.spinner("Agent running..."):
        for event_type, payload in process_claim(
            scenario_info["claim_id"],
            scenario_info["scenario"],
            soe,
        ):
            if event_type == "step":
                step = payload
                if step.enforcement == "allow" and not step.audit_override:
                    allow_count += 1
                elif step.enforcement == "deny":
                    deny_count += 1
                else:
                    escalate_count += 1

                steps.append({
                    "label": step.label(),
                    "enforcement": step.enforcement,
                    "audit": step.audit_override,
                    "latency": step.latency_ms,
                    "reason": step.reason[:100] if step.reason else "",
                })
                render_metrics()
                render_steps()
                time.sleep(0.3)  # brief pause for visual effect

            elif event_type == "final":
                with final_ph:
                    st.markdown(f"""
                    <div class="final-summary">
                      <div style="font-weight:700;font-size:1rem;margin-bottom:8px">📋 Agent Decision</div>
                      <div style="color:#374151">{payload}</div>
                    </div>
                    """, unsafe_allow_html=True)

    st.success(f"Done — {allow_count} allowed · {deny_count} denied · {escalate_count} audit overrides")

    # ── SOE Enforcement Layer ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### SOE Enforcement Layer")

    col_chronicle, col_arbiter = st.columns(2)

    with col_chronicle:
        st.markdown("#### 📜 Chronicle — Audit Trail")
        with st.spinner("Fetching audit events..."):
            audit = soe.get_audit_events(scenario_info["claim_id"].lower().replace("-", "") if False else "claims-processor")
            events = audit.get("events", [])
        if events:
            st.caption(f"{len(events)} events logged to immutable audit trail")
            for e in events[-6:]:
                dec = e.get("originalDecision") or e.get("decision", "?")
                icon = "✅" if dec == "allow" else "🚫"
                st.markdown(f"{icon} `{e.get('toolName','?')}` — {e.get('reason','')[:70]}")
        else:
            st.caption("No events yet — run a scenario first")

    with col_arbiter:
        st.markdown("#### ⚖️ Arbiter — Risk Analysis")
        if deny_count > 0:
            with st.spinner("Arbiter analyzing trajectory..."):
                trajectory = [
                    {"toolName": s["label"].split(":")[0], "decision": s["enforcement"],
                     "reason": s["reason"], "timestamp": "2026-04-28T00:00:00Z"}
                    for s in steps
                ]
                analysis = soe.arbiter_analyze("claims-processor", trajectory)

            if "error" not in analysis:
                risk_used = analysis.get("riskUsed", 0)
                risk_max = analysis.get("riskMax", 30)
                patterns = analysis.get("patterns", [])
                recommendations = analysis.get("recommendations", [])

                pct = min(int((risk_used / risk_max) * 100), 100) if risk_max else 0
                color = "#22c55e" if pct < 50 else "#f59e0b" if pct < 80 else "#ef4444"
                st.markdown(f"""
                <div style="margin-bottom:12px">
                  <div style="font-size:13px;color:#64748b;margin-bottom:4px">Risk Budget Used</div>
                  <div style="background:#e2e8f0;border-radius:6px;height:16px">
                    <div style="background:{color};width:{pct}%;height:16px;border-radius:6px"></div>
                  </div>
                  <div style="font-size:12px;color:{color};margin-top:4px;font-weight:600">{risk_used}/{risk_max} ({pct}%)</div>
                </div>
                """, unsafe_allow_html=True)
                if patterns:
                    st.caption("**Patterns detected:**")
                    for p in patterns[:3]:
                        st.markdown(f"- {p}")
                if recommendations:
                    st.caption("**Recommendations:**")
                    for r in recommendations[:2]:
                        st.markdown(f"- {r}")
            else:
                st.caption("Arbiter analysis not available")
        else:
            st.caption("No suspicious trajectory — Arbiter shows clean run ✓")
            risk = soe.get_risk_state("claims-processor")
            st.metric("Risk Used", f"{risk.get('riskUsed',0)} / {risk.get('riskMax',30)}", delta=None)
            st.caption(f"Status: {risk.get('status','normal').upper()}")

    if dashboard_url:
        st.markdown(f"\n[📊 View full SOE Dashboard with live feeds →]({dashboard_url})")

# ── SOE Definition Reference ──────────────────────────────────────────────────
with st.expander("📄 View Active SOE Definition for claims-processor"):
    st.json({
        "agentId": "claims-processor",
        "description": "Insurance claims processing agent. Read-only access to claims, policies, and medical codes. Cannot access PII or payment systems.",
        "identity": {
            "role": "InsuranceClaimsProcessor",
            "authorityLevel": "claims-adjuster",
            "environmentScope": ["development", "uat", "production"],
        },
        "dataAccess": {
            "readAllow": ["claims/**", "policies/**", "medical-codes/**", "fraud-rules/**"],
            "readDeny": ["customer/pii/**", "**/ssn*", "**/credentials*", "**/.env*", "**/secrets*", "config/db-*"],
            "writeAllow": ["claims/approved/**", "claims/denied/**", "claims/escalated/**", "reports/**"],
            "writeDeny": ["customer/**", "payments/**", "policies/**", "**/credentials*"],
        },
        "toolActions": {
            "allowed": ["read_file", "write_file"],
            "denied": [],
            "bash": {
                "allow": ["python scripts/fraud-check.py *", "python scripts/validate.py *"],
                "deny": ["rm -rf *", "DROP TABLE *", "DELETE FROM *", "curl * | sh", "sudo *"],
            },
            "execute_script": {
                "allow": ["python scripts/*", "node scripts/*"],
                "deny": ["rm *", "DROP *", "DELETE *", "sudo *"],
            },
            "query_database": {
                "allow": ["SELECT * FROM claim_history *", "SELECT fraud_score *", "SELECT pre_auth *"],
                "deny": ["DROP TABLE *", "DELETE FROM *", "UPDATE audit_log *", "INSERT INTO payments *"],
            },
        },
        "riskBudget": {
            "maxPerSession": 30,
            "thresholds": {"warn": 15, "throttle": 22, "critical": 27, "exhausted": 30},
        },
    })
