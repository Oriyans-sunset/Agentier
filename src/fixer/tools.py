import json

from langchain_core.tools import tool


class Tools:
    def __init__(self, findings_path: str, csv_path: str):
        self.findings_path = findings_path
        self.csv_path = csv_path
        try:
            with open(self.findings_path) as f:
                self._findings = json.load(f)
        except Exception as e:
            raise Exception(e)

    def get_all_tools(self) -> list:
        return [
            self.get_all_findings,
            self.get_finding_by_column,
            self.get_current_time,
            self.calculator,
            self.write_and_edit_file,
        ]

    @property
    def get_all_findings(self):
        ...

    @property
    def get_finding_by_column(self):
        ...

    @staticmethod
    @tool
    def get_current_time() -> str:
        ...

    @staticmethod
    @tool
    def calculator(expression: str) -> str:
        ...

    @staticmethod
    @tool
    def write_and_edit_file(content: str, filename: str, filetype: str = "txt") -> str:
        ...
