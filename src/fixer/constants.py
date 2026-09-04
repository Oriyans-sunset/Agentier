import os

MODEL = "claude-sonnet-5"
LOG_PATH = os.path.join(os.path.dirname(__file__), "logs", "fixer_logs.json")
DATA_SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "fake-data", "data.csv")
INVESTIGATION_RESULT_PATH = os.path.join(os.path.dirname(__file__), "..", "schemas", "findings.json")
FIXER_RESULT_PATH = os.path.join(os.path.dirname(__file__), "..", "schemas", "fixer_response.json")

SYSTEM_PROMPT = ""
