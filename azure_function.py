import json
import logging
import azure.functions as func
import os
from processor import QuestionProcessor, ValidationError




class OutputFormatter:
    def __init__(self, format_name: str = 'json'):
        import outputOptions  # Import here to avoid issues in Azure Functions
        self.outputOptions = outputOptions
        self.format_name = format_name
        self.output_func = outputOptions.get_output_function(format_name)

    def format(self, content, options=None):
        # options is ignored except for 'filename', which is not used in Azure Functions
        # Instead, always return the formatted string or bytes
        if self.format_name == 'json':
            return json.dumps(content, indent=2)
        elif self.format_name == 'excel':
            # Return Excel as bytes
            import io
            import pandas as pd
            df = pd.DataFrame(content)
            if 'citations' in df.columns:
                citations = pd.DataFrame(df['citations'].tolist()).fillna('')
                df = df.drop('citations', axis=1)
                df = pd.concat([df[['question', 'answer']], citations], axis=1)
                df.columns = ['Question', 'Answer'] + [f'Cite {i+1}' for i in range(citations.shape[1])]
            else:
                df = df[['question', 'answer']]
                df.columns = ['Question', 'Answer']
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer) as writer:
                df.to_excel(writer, index=False)
            buffer.seek(0)
            return buffer.read()
        else:
            # Fallback to raw
            return str(content)


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Azure Function HTTP trigger entry point."""
    try:
        req_json = req.get_json()
    except Exception:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON in request body."}),
            status_code=400,
            mimetype="application/json"
        )

    base_url = req_json.get('base_url')
    questions_data = req_json.get('questions')
    debug = req_json.get('debug', False)
    endpoint = req_json.get('endpoint')
    output_format = req_json.get('format', 'json')
    
    if not base_url or not questions_data:
        return func.HttpResponse(
            json.dumps({"error": "'base_url' and 'questions' are required in the request body."}),
            status_code=400,
            mimetype="application/json"
        )
    
    try:
        processor = QuestionProcessor(base_url, endpoint=endpoint, debug=debug)
        questions = processor.get_questions_from_body(questions_data)
        results = processor.process_questions(questions)
    except ValidationError as e:
        return func.HttpResponse(
            json.dumps({"error": f"Validation error: {e}"}),
            status_code=400,
            mimetype="application/json"
        )
    except Exception as e:
        logging.exception("Failed to process questions")
        return func.HttpResponse(
            json.dumps({"error": f"Failed to process questions: {e}"}),
            status_code=500,
            mimetype="application/json"
        )
    
    formatter = OutputFormatter(output_format)
    formatted = formatter.format(results)
    
    if output_format == 'excel':
        return func.HttpResponse(
            formatted,
            status_code=200,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                'Content-Disposition': 'attachment; filename="results.xlsx"'
            }
        )
    else:
        return func.HttpResponse(
            formatted,
            status_code=200,
            mimetype="application/json"
        )
