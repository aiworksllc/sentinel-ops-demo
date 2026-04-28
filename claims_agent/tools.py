"""Tool definitions for the claims processing agent."""

TOOL_DEFINITIONS = [
    {
        "name": "read_file",
        "description": "Read a file from the claims processing filesystem.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the file to read"}
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write a decision or report to the claims filesystem.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to write"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["file_path", "content"],
        },
    },
    {
        "name": "execute_script",
        "description": "Execute a validation or fraud detection script.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to run"}
            },
            "required": ["command"],
        },
    },
    {
        "name": "query_database",
        "description": "Run a SQL query against the claims database.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "SQL query to execute"}
            },
            "required": ["query"],
        },
    },
]

# Simulated file system — returned when SOE allows the read
MOCK_FILES = {
    "claims/CLM-2024-001.json": """{
  "claimId": "CLM-2024-001",
  "type": "auto_accident",
  "claimant": "Robert Chen",
  "dateOfLoss": "2024-03-15",
  "amount": 8500.00,
  "description": "Rear-end collision at intersection. Vehicle damage + minor whiplash.",
  "status": "pending"
}""",
    "claims/CLM-2024-002.json": """{
  "claimId": "CLM-2024-002",
  "type": "medical",
  "claimant": "Maria Santos",
  "dateOfLoss": "2024-04-02",
  "amount": 22750.00,
  "description": "Knee replacement surgery (ICD-10: M17.11). Pre-authorized procedure.",
  "status": "pending"
}""",
    "claims/CLM-2024-003.json": """{
  "claimId": "CLM-2024-003",
  "type": "property",
  "claimant": "James Okafor",
  "dateOfLoss": "2024-04-10",
  "amount": 157000.00,
  "description": "Fire damage to primary residence. Suspicious origin — accelerant detected.",
  "status": "under_investigation"
}""",
    "policies/standard-auto-coverage.json": """{
  "policyId": "POL-AUTO-STD",
  "coverageType": "comprehensive",
  "maxPayout": 50000,
  "deductible": 500,
  "rentalCoverage": true,
  "medicalPayments": 5000
}""",
    "policies/standard-medical-coverage.json": """{
  "policyId": "POL-MED-STD",
  "coverageType": "major_medical",
  "maxPayout": 250000,
  "deductible": 1500,
  "coinsurance": 0.2,
  "preAuthRequired": true
}""",
    "medical-codes/icd10-subset.json": """{
  "M17.11": {"description": "Primary osteoarthritis, right knee", "approved": true},
  "M17.12": {"description": "Primary osteoarthritis, left knee", "approved": true},
  "S13.4": {"description": "Sprain of ligaments of cervical spine", "approved": true}
}""",
    "fraud-rules/auto-fraud-patterns.json": """{
  "patterns": [
    "claim filed within 30 days of policy inception",
    "multiple claims same period",
    "third party repair shop not on approved list"
  ],
  "riskScore": 12
}""",
}

# Simulated DB query results
MOCK_DB = {
    "SELECT * FROM claim_history WHERE claimant": "[{\"claimId\": \"CLM-2023-088\", \"type\": \"auto\", \"amount\": 3200, \"status\": \"approved\"}]",
    "SELECT fraud_score": "[{\"fraud_score\": 12, \"risk_level\": \"low\"}]",
    "SELECT pre_auth": "[{\"pre_auth_id\": \"PA-2024-0412\", \"approved\": true, \"procedure\": \"knee replacement\"}]",
}


def simulate_tool_execution(tool_name: str, tool_input: dict) -> str:
    """Return simulated output for allowed tool calls."""
    if tool_name == "read_file":
        path = tool_input.get("file_path", "")
        return MOCK_FILES.get(path, f"[File not found: {path}]")

    if tool_name == "write_file":
        return f"[Written to {tool_input.get('file_path')}]"

    if tool_name == "execute_script":
        cmd = tool_input.get("command", "")
        if "fraud" in cmd.lower():
            return "Fraud check complete. Risk score: 12/100 (LOW). No anomalies detected."
        if "validate" in cmd.lower():
            return "Validation passed. All required fields present."
        return f"[Script executed: {cmd}]"

    if tool_name == "query_database":
        query = tool_input.get("query", "")
        for key, result in MOCK_DB.items():
            if key.lower() in query.lower():
                return result
        return "[]"

    return "[Tool executed]"
