import json
from datetime import datetime

from langchain_core.tools import tool


class Tools:
    def __init__(self, file: str):
        self.file = file
        try:
            with open(self.file) as f:
                self._profiled_schema = json.load(f)["columns"]
        except Exception as e:
            raise Exception(e)

    def get_all_tools(self) -> list:
        return [
            self.execute_python,
            self.get_all_columns,
            self.get_column_info,
            self.calculator,
            self.write_and_edit_file,
            self.get_current_time,
        ]

    @property
    def get_all_columns(self):
        schema = self._profiled_schema

        @tool
        def _get_all_columns() -> dict[str, str]:
            """Returns the number and names of all columns in the CSV file."""
            return {
                key: value["name"]
                for key, value in schema.items()
                if key != "number_of_columns"
            }

        return _get_all_columns

    @property
    def get_column_info(self):
        schema = self._profiled_schema

        @tool
        def _get_column_info(column: str) -> dict:
            """Returns the full profiled information for a single column, given its name."""
            for value in schema.values():
                if isinstance(value, dict) and value.get("name") == column:
                    return value
            return {"error": f"Column '{column}' not found."}

        return _get_column_info

    @property
    def execute_python(code: str):
        pass

    @staticmethod
    @tool
    def calculator(expression: str) -> str:
        """Evaluate a basic arithmetic expression, e.g. '12 * (3 + 4)'.
        Only supports +, -, *, /, parentheses, and numbers.
        """
        allowed = set("0123456789+-*/(). ")
        if not set(expression) <= allowed:
            return "Error: expression contains unsupported characters."
        try:
            return str(eval(expression, {"__builtins__": {}}, {}))
        except Exception as e:
            return f"Error: {e}"

    @staticmethod
    @tool
    def write_and_edit_file(content: str, filename: str, filetype: str = "txt") -> str:
        """
        Writes a new file if the file does not exist OR appends to an existing file with the given filename, filetype and content.
        Defaults to .txt filetype unless specified.
        """
        if not content:
            return "Error: content cannot be empty."
        f_name = filename + "." + filetype
        with open(f_name, "+a") as f:
            f.write(content)

        return f"File {f_name} successfully written."

    @staticmethod
    @tool
    def get_current_time() -> str:
        """Return the current date and time."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
