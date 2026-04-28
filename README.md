# ClaimGuard AI — Sentinel-Ops SOE Demo

Insurance claims processing agent protected by a **Safe Operating Envelope (SOE)**. Every tool call the AI agent makes is evaluated against the SOE in real time — allowed actions proceed, blocked actions are rejected with an audit trail.

## What This Demos

| Scenario | What Happens |
|----------|-------------|
| ✅ Straightforward Approval | Agent reads claim + policy, runs fraud check, writes decision — all within SOE |
| 🔒 PII Protection | Agent attempts to access raw SSN/PII — blocked. Claim processed using only approved data paths |
| 🚨 Rogue Behavior Blocked | Agent tries to DELETE audit logs and steal DB credentials — all blocked and logged |

## Architecture

```
Streamlit UI
    │
    ▼
ClaimGuard Agent (Claude claude-haiku-4-5)
    │  For every tool call:
    ├──► Sentinel-Ops SOE API  ──► ALLOW / DENY
    │        (< 1ms deterministic)
    ▼
Tool executes (if allowed) or returns blocked message
    │
    ▼
SOE Dashboard shows full audit trail
```

## Setup

```bash
# 1. Clone and install
git clone https://github.com/aiworksllc/sentinel-ops-demo
cd sentinel-ops-demo
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your keys:
#   ANTHROPIC_API_KEY=sk-ant-...
#   SOE_API_URL=http://your-soe-stack/
#   SOE_API_KEY=your-api-key

# 3. Deploy the claims-processor SOE policy
python soe_setup.py

# 4. Run the demo
streamlit run streamlit_app.py
```

## SOE Policy for Claims Processor

The `claims-processor` agent is constrained to:

**Allowed reads:** `claims/**`, `policies/**`, `medical-codes/**`, `fraud-rules/**`

**Blocked reads:** `customer/pii/**`, `**/ssn*`, `**/credentials*`, `config/db-*`

**Allowed writes:** `claims/approved/**`, `claims/denied/**`, `claims/escalated/**`

**Blocked writes:** `customer/**`, `payments/**`, `policies/**`

**Allowed scripts:** `python scripts/fraud-check.py`, `python scripts/validate.py`

**Blocked commands:** `rm -rf *`, `DROP TABLE *`, `DELETE FROM *`, `curl * | sh`

## SOE Dashboard

After running scenarios, open the SOE Dashboard to see the full audit trail:

```
http://your-soe-stack/dashboard
```
