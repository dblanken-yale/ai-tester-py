"""
Azure Function implementation for AI Tester.

This module contains only the Azure Functions wiring/decorators.
All business logic is in the AzureFunctionHandler.
"""
import azure.functions as func
import sys
from pathlib import Path

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.azure.handlers import AzureFunctionHandler

# Create the FunctionApp instance
app = func.FunctionApp()

@app.timer_trigger(
    schedule="%AI_TESTER_SCHEDULE%", 
    arg_name="question_processor_timer", 
    run_on_startup=True, 
    use_monitor=False
)
def timer_process_batch_questions(question_processor_timer: func.TimerRequest) -> None:
    """
    Azure Function timer trigger for processing AI questions.
    
    This is just the Azure Functions decorator/wiring.
    All business logic is delegated to AzureFunctionHandler.
    
    Args:
        question_processor_timer: Azure Functions timer request object
    """
    handler = AzureFunctionHandler()
    success = handler.handle_timer_trigger(question_processor_timer)
    
    # Azure Functions can raise exceptions to indicate failure
    if not success:
        raise RuntimeError("Question processing failed")