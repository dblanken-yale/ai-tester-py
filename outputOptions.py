import pandas as pd
import io
import sys
import json
from openpyxl import load_workbook
from openpyxl.styles import Alignment
from typing import Any, Callable, Dict, List, Optional

# Output format registry for flexibility
output_registry: Dict[str, Callable[[Any, Dict[str, Any]], None]] = {}

def register_output_format(name: str):
    """Decorator to register a new output format."""
    def decorator(func: Callable[[Any, Dict[str, Any]], None]):
        output_registry[name] = func
        return func
    return decorator

@register_output_format('json')
def to_json(results: List[dict], options: Dict[str, Any]) -> None:
    """Converts the results to JSON format and writes it to a file or prints it to the console."""
    if 'filename' in options and options['filename'] is not None:
        with open(options['filename'], 'w') as file:
            json.dump(results, file)
    else:
        print(json.dumps(results, indent=2))

@register_output_format('excel')
def to_excel(content: List[dict], options: Dict[str, Any]) -> None:
    """Converts the results to an Excel file and writes it to a file or prints it to the console."""
    df = pd.DataFrame(content)
    # Handle missing or empty citations gracefully
    if 'citations' in df.columns:
        citations = pd.DataFrame(df['citations'].tolist()).fillna('')
        df = df.drop('citations', axis=1)
        df = pd.concat([df[['question', 'answer']], citations], axis=1)
        df.columns = ['Question', 'Answer'] + [f'Cite {i+1}' for i in range(citations.shape[1])]
    else:
        df = df[['question', 'answer']]
        df.columns = ['Question', 'Answer']
    if 'filename' in options and options['filename'] is not None:
        filename = options['filename']
        df.to_excel(filename, index=False)
        resize_excel(filename)
        print("Data written to file: ", filename)
    else:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer) as writer:
            df.to_excel(writer, index=False)
        buffer.seek(0)
        sys.stdout.buffer.write(buffer.read())

@register_output_format('raw')
def to_raw(content: Any, _options: Dict[str, Any]) -> None:
    """Prints the raw content to the console."""
    print(content)

def get_output_function(format_name: str) -> Callable[[Any, Dict[str, Any]], None]:
    """Get the output function for a given format name."""
    return output_registry.get(format_name, to_raw)

def resize_excel(filename: str) -> None:
    """Resizes the columns and rows in the Excel file."""
    workbook = load_workbook(filename)
    sheet = workbook.active
    sheet.column_dimensions['B'].width = 140
    sheet.column_dimensions['C'].width = 30
    for row in sheet.iter_rows():
        for cell in row:
            if cell.column_letter in ['B', 'C']:
                cell.alignment = Alignment(vertical='top', wrap_text=True)
                sheet.row_dimensions[cell.row].height = None
            else:
                cell.alignment = Alignment(vertical='top')
    workbook.save(filename)
