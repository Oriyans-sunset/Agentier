from langchain_core.tools import tool
from datetime import datetime

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


@tool
def get_current_time() -> str:
    """Return the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")