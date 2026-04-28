"""SOE client — evaluates tool calls against the Sentinel-Ops API."""
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

SOE_API_URL = os.getenv("SOE_API_URL", "http://soe-sentinel-ops-1280026220.us-east-1.elb.amazonaws.com")
SOE_API_KEY = os.getenv("SOE_API_KEY", "")


class SOEClient:
    def __init__(self, api_url: str = SOE_API_URL, api_key: str = SOE_API_KEY):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-SOE-Api-Key": api_key, "Content-Type": "application/json"}

    def evaluate(self, agent_id: str, tool_name: str, tool_input: dict) -> dict:
        start = time.monotonic()
        try:
            resp = requests.post(
                f"{self.api_url}/v1/evaluate",
                json={"agentId": agent_id, "toolName": tool_name, "toolInput": tool_input},
                headers=self.headers,
                timeout=10,
            )
            data = resp.json()
        except Exception as e:
            data = {"decision": "deny", "reason": f"SOE unreachable: {e}", "layer": "error"}
        data["_latency_ms"] = round((time.monotonic() - start) * 1000)
        enforcement = data.get("originalDecision") or data.get("decision", "deny")
        data["_enforcement"] = enforcement
        return data

    def deploy(self, soe_definition: dict) -> dict:
        resp = requests.post(
            f"{self.api_url}/v1/deploy",
            json={"soe": soe_definition},
            headers=self.headers,
            timeout=10,
        )
        return resp.json()

    def health(self) -> bool:
        try:
            resp = requests.get(f"{self.api_url}/v1/health", timeout=5)
            return resp.json().get("status") == "HEALTHY"
        except Exception:
            return False
