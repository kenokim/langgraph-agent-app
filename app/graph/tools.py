from langchain_core.tools import tool

@tool
def magic_word_tool(input_str: str) -> str:
    """Returns a magic phrase including the input string."""
    return f"The magic word for '{input_str}' is Alakazam!"

@tool
def add_numbers_tool(a: int, b: int) -> int:
    """Adds two numbers together."""
    return a + b

custom_tools = [magic_word_tool, add_numbers_tool] 