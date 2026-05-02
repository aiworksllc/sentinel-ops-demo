"""Deploy the claims-processor SOE definition to the Sentinel-Ops API."""
import os
import sys
from dotenv import load_dotenv
from claims_agent.soe_client import SOEClient

load_dotenv()

SOE_DEFINITION = {
    "agentId": "claims-processor",
    "version": "3.2.0",
    "mode": "enforce",
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
            "**/credential*",
            "**/.env*",
            "**/secrets*",
            "config/**",
            "**/password*",
            "**/db-*",
        ],
        "writeAllow": [
            "claims/approved/**",
            "claims/denied/**",
            "claims/escalated/**",
            "decisions/**",
            "reports/**",
        ],
        "writeDeny": [
            "customer/**",
            "payments/**",
            "policies/**",
            "**/credentials*",
            "**/.env*",
            "audit/**",
        ],
    },
    "toolActions": {
        "bash": {
            "allow": [
                "python*fraud*",
                "python3*fraud*",
                "python*validate*",
                "python3*validate*",
                "grep * claims*",
                "grep * policies*",
                "psql -c \"SELECT*",
            ],
            "deny": [
                "rm -rf *",
                "rm *",
                "DROP TABLE*",
                "DELETE FROM*",
                "psql -c \"DELETE*",
                "psql -c \"DROP*",
                "psql -c \"UPDATE audit*",
                "curl * | sh",
                "sudo *",
                "cat /etc/*",
                "cat config/*",
            ],
        },
    },
    "riskBudget": {
        "maxPerSession": 1000,
        "thresholds": {"warn": 500, "throttle": 750, "critical": 900, "exhausted": 1000},
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
        print(f"SUCCESS: SOE deployed for agent '{SOE_DEFINITION['agentId']}' v{SOE_DEFINITION['version']}")
    else:
        print(f"FAILED: {result}")
        sys.exit(1)


if __name__ == "__main__":
    main()
