"""Deploy the claims-processor SOE definition to the Sentinel-Ops API."""
import os
import sys
from dotenv import load_dotenv
from claims_agent.soe_client import SOEClient

load_dotenv()

SOE_DEFINITION = {
    "agentId": "claims-processor",
    "version": "1.0.0",
    "description": "Insurance claims processing agent. Read-only access to claims, policies, and medical codes. Cannot access PII or payment systems.",
    "identity": {
        "role": "InsuranceClaimsProcessor",
        "allowedPersonas": ["claims-processor"],
        "authorityLevel": "claims-adjuster",
        "environmentScope": ["development", "uat", "production"],
        "dataClassification": "confidential",
    },
    "dataAccess": {
        "readAllow": ["claims/**", "policies/**", "medical-codes/**", "fraud-rules/**"],
        "readDeny": [
            "customer/pii/**",
            "**/ssn*",
            "**/social-security*",
            "**/credentials*",
            "**/.env*",
            "**/secrets*",
            "config/db-*",
            "**/password*",
        ],
        "writeAllow": [
            "claims/approved/**",
            "claims/denied/**",
            "claims/escalated/**",
            "reports/**",
        ],
        "writeDeny": [
            "customer/**",
            "payments/**",
            "policies/**",
            "**/credentials*",
            "**/.env*",
        ],
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
            "allow": [
                "SELECT * FROM claim_history*",
                "SELECT fraud_score*",
                "SELECT pre_auth*",
            ],
            "deny": [
                "DROP TABLE*",
                "DELETE FROM*",
                "UPDATE audit_log*",
                "INSERT INTO payments*",
            ],
        },
    },
    "riskBudget": {
        "maxPerSession": 30,
        "thresholds": {"warn": 15, "throttle": 22, "critical": 27, "exhausted": 30},
    },
}


def main():
    soe = SOEClient()
    print(f"Connecting to {soe.api_url} ...")

    if not soe.health():
        print("ERROR: Cannot reach SOE API. Check SOE_API_URL and SOE_API_KEY in .env")
        sys.exit(1)

    print("Deploying claims-processor SOE definition ...")
    result = soe.deploy(SOE_DEFINITION)

    if result.get("deployed"):
        print(f"SUCCESS: SOE deployed for agent '{SOE_DEFINITION['agentId']}'")
    else:
        print(f"FAILED: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()
