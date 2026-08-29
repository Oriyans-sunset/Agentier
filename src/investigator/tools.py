import contextlib
import io
import json
from datetime import datetime

import numpy as np
import pandas as pd
from langchain_core.tools import tool


class Tools:
    def __init__(self, file: str, csv_path: str):
        self.file = file
        self.csv_path = csv_path
        try:
            with open(self.file) as f:
                self._profiled_schema = json.load(f)["columns"]
        except Exception as e:
            raise Exception(e)
        self._df = pd.read_csv(self.csv_path)
        self._exec_namespace = {
            "df": self._df.copy(),
            "pd": pd,
            "np": np,
            "__builtins__": __builtins__,
        }

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
    def execute_python(self):
        ns = self._exec_namespace
        original_df = self._df.copy()

        @tool
        def _execute_python(code: str) -> str:
            """Execute a Python code snippet to analyse the dataset.

            The variable `df` is a pandas DataFrame of the raw CSV, available in
            the execution namespace. Treat `df` as immutable — do not modify it
            in place. You may create derived DataFrames, Series, variables, and
            intermediate analysis results (e.g. df_clean = df.copy()). These
            objects persist across execute_python calls and may be reused in
            subsequent investigations.

            `pd` (pandas) and `np` (numpy) are also available.

            Print any results you want returned; the tool captures stdout and
            returns it as a string. Exceptions are caught and returned as an
            error message.

            Example:
                df_prices = df['price'].dropna()
                print(df_prices.describe())
            """
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    exec(code, ns)  # noqa: S102
                output = buf.getvalue()
            except Exception as e:
                output = f"Error: {type(e).__name__}: {e}"
            finally:
                ns["df"] = original_df.copy()
            return output if output.strip() else "(no output)"

        return _execute_python

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
