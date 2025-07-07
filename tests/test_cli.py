"""
Tests for CLI functionality.
"""

import pytest
import sys
from unittest.mock import patch, Mock
from argparse import Namespace

from src.cli.main import main, parse_args


class TestCLIArguments:
    """Test CLI argument parsing."""
    
    def test_parse_args_minimal(self):
        """Test parsing minimal required arguments."""
        with patch.object(sys, 'argv', ['test_cli.py', 'https://test.example.com']):
            args = parse_args()
        
        assert args.url == 'https://test.example.com'
        assert args.questions == './questions.yml'
        assert args.source_type == 'yaml'
        assert args.format == 'json'
        assert args.outfile is None
        assert args.debug is False
        assert args.endpoint == '/conversation'
    
    def test_parse_args_full(self):
        """Test parsing all possible arguments."""
        with patch.object(sys, 'argv', [
            'test_cli.py',
            'https://test.example.com',
            '--questions', 'custom.yml',
            '--source-type', 'dummy',
            '--format', 'excel',
            '--outfile', 'results.xlsx',
            '--debug',
            '--endpoint', '/api/test'
        ]):
            args = parse_args()
        
        assert args.url == 'https://test.example.com'
        assert args.questions == 'custom.yml'
        assert args.source_type == 'dummy'
        assert args.format == 'excel'
        assert args.outfile == 'results.xlsx'
        assert args.debug is True
        assert args.endpoint == '/api/test'
    
    def test_parse_args_short_flags(self):
        """Test parsing with short flag options."""
        with patch.object(sys, 'argv', [
            'test_cli.py',
            'https://test.example.com',
            '-q', 'test.yml',
            '-f', 'excel',
            '-o', 'output.xlsx',
            '-d',
            '-e', '/api'
        ]):
            args = parse_args()
        
        assert args.url == 'https://test.example.com'
        assert args.questions == 'test.yml'
        assert args.format == 'excel'
        assert args.outfile == 'output.xlsx'
        assert args.debug is True
        assert args.endpoint == '/api'
    
    def test_parse_args_legacy_filename(self):
        """Test parsing with legacy filename argument."""
        with patch.object(sys, 'argv', [
            'test_cli.py',
            'https://test.example.com',
            '--filename', 'legacy_output.json'
        ]):
            args = parse_args()
        
        assert args.url == 'https://test.example.com'
        assert args.filename == 'legacy_output.json'
    
    def test_parse_args_help(self):
        """Test that help argument works."""
        with patch.object(sys, 'argv', ['test_cli.py', '--help']):
            with pytest.raises(SystemExit):
                parse_args()
    
    def test_parse_args_missing_url(self):
        """Test parsing with missing required URL."""
        with patch.object(sys, 'argv', ['test_cli.py']):
            with pytest.raises(SystemExit):
                parse_args()


class TestCLIMain:
    """Test CLI main function."""
    
    @patch('src.cli.main.QuestionProcessingService')
    def test_main_success(self, mock_service_class):
        """Test successful CLI execution."""
        # Mock service instance
        mock_service = Mock()
        mock_service.process_questions.return_value = True
        mock_service_class.return_value = mock_service
        
        # Mock sys.argv
        test_args = ['test_questions.py', 'https://test.example.com']
        
        with patch.object(sys, 'argv', test_args):
            main()
        
        # Success case doesn't raise SystemExit
        mock_service.process_questions.assert_called_once()
    
    @patch('src.cli.main.QuestionProcessingService')
    def test_main_processing_failure(self, mock_service_class):
        """Test CLI execution with processing failure."""
        # Mock service instance that fails
        mock_service = Mock()
        mock_service.process_questions.return_value = False
        mock_service_class.return_value = mock_service
        
        test_args = ['test_questions.py', 'https://test.example.com']
        
        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            result = exc_info.value.code
        
        assert result == 1
        mock_service.process_questions.assert_called_once()
    
    @patch('src.cli.main.QuestionProcessingService')
    def test_main_exception_handling(self, mock_service_class):
        """Test CLI exception handling."""
        # Mock service that raises exception
        mock_service_class.side_effect = Exception("Test error")
        
        test_args = ['test_questions.py', 'https://test.example.com']
        
        with patch.object(sys, 'argv', test_args):
            with pytest.raises(SystemExit) as exc_info:
                main()
            result = exc_info.value.code
        
        assert result == 1
    
    @patch('src.cli.main.QuestionProcessingService')
    def test_main_with_debug(self, mock_service_class):
        """Test CLI execution with debug enabled."""
        mock_service = Mock()
        mock_service.process_questions.return_value = True
        mock_service_class.return_value = mock_service
        
        test_args = ['test_questions.py', 'https://test.example.com', '--debug']
        
        with patch.object(sys, 'argv', test_args):
            main()
        
        # Success case doesn't raise SystemExit
        # Verify config was created with debug=True
        call_args = mock_service_class.call_args[0][0]
        assert call_args.debug is True
    
    @patch('src.cli.main.QuestionProcessingService')
    def test_main_with_custom_options(self, mock_service_class):
        """Test CLI execution with custom options."""
        mock_service = Mock()
        mock_service.process_questions.return_value = True
        mock_service_class.return_value = mock_service
        
        test_args = [
            'test_questions.py',
            'https://custom.example.com',
            '--questions', 'custom.yml',
            '--source-type', 'dummy',
            '--format', 'excel',
            '--outfile', 'results.xlsx',
            '--endpoint', '/api/custom'
        ]
        
        with patch.object(sys, 'argv', test_args):
            main()
        
        # Success case doesn't raise SystemExit
        # Verify config was created with custom options
        call_args = mock_service_class.call_args[0][0]
        assert call_args.base_url == 'https://custom.example.com'
        assert call_args.endpoint == '/api/custom'
        assert call_args.question_source.source_type == 'dummy'
        assert call_args.question_source.file_path == 'custom.yml'
        assert call_args.output_destination.destination_type == 'excel'
        assert call_args.output_destination.file_path == 'results.xlsx'
    
    @patch('src.cli.main.QuestionProcessingService')
    def test_main_legacy_filename_support(self, mock_service_class):
        """Test CLI with legacy filename argument."""
        mock_service = Mock()
        mock_service.process_questions.return_value = True
        mock_service_class.return_value = mock_service
        
        test_args = [
            'test_questions.py',
            'https://test.example.com',
            '--filename', 'legacy_output.json'
        ]
        
        with patch.object(sys, 'argv', test_args):
            main()
        
        # Success case doesn't raise SystemExit
        # Verify legacy filename was used
        call_args = mock_service_class.call_args[0][0]
        assert call_args.output_destination.file_path == 'legacy_output.json'


class TestCLIIntegration:
    """Test CLI integration with other components."""
    
    @patch('src.cli.main.QuestionProcessingService')
    def test_config_creation_from_args(self, mock_service_class):
        """Test that CLI arguments are properly converted to config."""
        mock_service = Mock()
        mock_service.process_questions.return_value = True
        mock_service_class.return_value = mock_service
        
        # Create mock args
        args = Namespace(
            url='https://test.example.com',
            endpoint='/api',
            debug=True,
            questions='test.yml',
            source_type='yaml',
            format='json',
            outfile='output.json',
            filename=None,
            postgres_connection=None,
            postgres_table='ai_results'
        )
        
        # Test config creation
        with patch('src.cli.main.parse_args', return_value=args):
            with patch.object(sys, 'argv', ['test_questions.py']):
                main()
        
        # Success case doesn't raise SystemExit
        # Verify service was called with correct config
        mock_service_class.assert_called_once()
        config = mock_service_class.call_args[0][0]
        
        assert config.base_url == 'https://test.example.com'
        assert config.endpoint == '/api'
        assert config.debug is True
        assert config.question_source.source_type == 'yaml'
        assert config.question_source.file_path == 'test.yml'
        assert config.output_destination.destination_type == 'json'
        assert config.output_destination.file_path == 'output.json'