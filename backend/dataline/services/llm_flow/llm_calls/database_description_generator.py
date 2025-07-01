
def database_description_generator_prompt(table: str, columns: list[dict]) -> str:
    col_list = "\n".join([f"- {col['name']} ({col['type']})" for col in columns])
    return f"""
    You are a data architect. Given the following table name and list of columns, write:
    1. A 1-line description of what the table represents.
    2. A one-line description for each column.
    
    Table name: {table}
    Columns:
    {col_list}
    
    Respond in JSON format like:
    {{
      "tableDescription": "...",
      "columns": {{
        "column1": "...",
        "column2": "..."
      }}
    }}
    Only return valid JSON. Do not include any explanations or formatting.
    """
