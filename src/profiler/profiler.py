import json
import os
import pandas as pd

class Profiler:
    _target_schema = {}
    _profiled_schema = {}
    _df = None

    def __init__(self, target_schema_path: str):
        self.target_schema_path = target_schema_path
        self._load_json(target_schema_path)

    def _load_json(self, path: str) -> None:
        """Loads json from a file path into a variable"""
        with open(path, "r") as f:
            self._target_schema = json.load(f)

        
    def try_integer(value):
        try:
            number = float(str(value).strip())

            # 10.0 is integer-compatible, 10.5 isnt
            return number.is_integer()
        except (ValueError, TypeError):
            return False


    def try_float(value):
        try:
            float(str(value).strip())
            return True
        except (ValueError, TypeError):
            return False


    def try_boolean(value):
        normalized = str(value).strip().lower()

        return normalized in {
            "true",
            "false",
            "yes",
            "no",
            "1",
            "0"
        }


    def try_date(value):
        try:
            pd.to_datetime(value)
            return True
        except (ValueError, TypeError):
            return False

    PARSERS = {
        "integer": try_integer,
        "float": try_float,
        "boolean": try_boolean,
        "date": try_date,
    }

    def _get_type_parsing_statistics(self, column_name: str) -> dict[str, dict[str, int]]: 
        values = self._df[column_name].dropna()

        statistics = {}

        for type_name, parser in self.PARSERS.items():

            success_count = 0
            failure_count = 0

            for value in values:
                if parser(value):
                    success_count += 1
                else:
                    failure_count += 1

            total = len(values)

            statistics[type_name] = {
                "success_count": success_count,
                "failure_count": failure_count,
                "success_rate": (
                    success_count / total
                    if total > 0
                    else 0
                )
            }

        return statistics

    def generate_profiled_schema(self) -> str:
        """Returns a path to a profiled schema file"""
        data_path = os.path.join(os.path.dirname(__file__), "..", "fake-data", "data.csv")
        self._df = pd.read_csv(data_path)
        print(self._df) 
        number_of_columns = len(self._df.columns)
        self._profiled_schema["columns"] = {"number_of_columns": number_of_columns}

        for i in range(number_of_columns):
            column_number = f"column_{i+1}"
            column_name = self._df.columns[i]
            column = self._df[column_name]
            total_count = len(column)
            null_count = column.isnull().sum()
            self._profiled_schema["columns"][column_number] = {
                "name": column_name,
                "column_type_analysis": {
                    "pandas_dtype": str(column.dtype),
                    "manual_type_parsing_statistics": self._get_type_parsing_statistics(column_name)
                },
                "total_value_count": total_count,
                "null_count": null_count,
                "null_percentage": null_count/total_count,
                "unique_value_count": len(column.unique())
                }
            
            if (("int" in str(column.dtype).lower()) or ("float" in str(column.dtype).lower())):
                self._profiled_schema["columns"][column_number]["min_value"] = column.min()
                self._profiled_schema["columns"][column_number]["max_value"] = column.max()
                self._profiled_schema["columns"][column_number]["mean"] = column.mean()
                self._profiled_schema["columns"][column_number]["median"] = column.median()
                self._profiled_schema["columns"][column_number]["standard_deviation"] = column.std()

        
        json_output = json.dumps(self._profiled_schema, default=lambda x: x.item() if hasattr(x, 'item') else str, indent=2)
        print(json_output)
        profiled_schema_path = os.path.join(os.path.dirname(__file__), "..", "schemas", "profiled_schema.json")
        with open(profiled_schema_path, "w") as file:
            file.write(json_output)
