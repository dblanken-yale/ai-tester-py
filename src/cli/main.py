"""Command-line interface for AI Tester."""
import argparse
import sys
import logging
from pathlib import Path

# Add the src directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import AITesterConfig
from src.services.question_service import QuestionProcessingService

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='AI Tester - Automated AI endpoint testing')
    
    # Required arguments
    parser.add_argument('url', help='Base URL of the AI endpoint to test')
    
    # Question source options
    parser.add_argument('--questions', '-q', 
                        help='Path to questions file (default: questions.yml)',
                        default='./questions.yml')
    parser.add_argument('--source-type',
                        choices=['yaml', 'dummy', 'postgresql'],
                        default='yaml',
                        help='Type of question source (default: yaml)')
    
    # Output options
    parser.add_argument('--format', '-f',
                        choices=['json', 'excel', 'console'],
                        default='json',
                        help='Output format (default: json)')
    parser.add_argument('--outfile', '-o',
                        help='Output file path (default: console output)')
    
    # Processing options
    parser.add_argument('--debug', '-d',
                        action='store_true',
                        help='Enable debug mode for detailed output')
    parser.add_argument('--endpoint', '-e',
                        help='API endpoint path (default: /conversation)',
                        default='/conversation')
    
    # Legacy compatibility
    parser.add_argument('--filename',
                        help='Legacy alias for --outfile')
    
    return parser.parse_args()


def main():
    """Main entry point for CLI."""
    try:
        args = parse_args()
        
        # Handle legacy filename argument
        if args.filename and not args.outfile:
            args.outfile = args.filename
        
        # Create configuration from CLI arguments
        config = AITesterConfig.from_cli_args(args)
        
        # Create and run the question processing service
        service = QuestionProcessingService(config)
        success = service.process_questions()
        
        if not success:
            logger.error("Question processing failed")
            sys.exit(1)
        
        logger.info("Question processing completed successfully")
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()