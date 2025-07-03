"""Azure Function implementation for AI Tester."""
import logging
import azure.functions as func
import sys
from pathlib import Path

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import AITesterConfig
from src.services.question_service import QuestionProcessingService

logging.basicConfig(level=logging.INFO)
app = func.FunctionApp()


@app.timer_trigger(schedule="%AI_TESTER_SCHEDULE%", arg_name="question_processor_timer", run_on_startup=True, use_monitor=False)
def timer_process_batch_questions(question_processor_timer: func.TimerRequest) -> None:
    """Azure Function timer trigger for processing questions."""
    if question_processor_timer.past_due:
        logging.info('The question processor timer is past due!')

    logging.info('Azure Function timer trigger started processing questions')
    
    try:
        # Create configuration from environment variables
        config = AITesterConfig.from_environment()
        
        # Log configuration information
        logging.info(f'Using question source: {config.question_source.source_type}')
        logging.info(f'Using output destination: {config.output_destination.destination_type}')
        logging.info(f'Base URL: {config.base_url}')
        logging.info(f'Debug mode: {config.debug}')
        
        # Create and run the question processing service
        service = QuestionProcessingService(config)
        success = service.process_questions()
        
        if success:
            logging.info('Question processing completed successfully')
        else:
            logging.error('Question processing failed')
            
    except Exception as e:
        logging.error(f'Question processing failed with exception: {e}', exc_info=True)