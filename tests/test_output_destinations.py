"""
Tests for output destinations.
"""

import pytest
import tempfile
import os
import json
from unittest.mock import patch, Mock

from src.core.output_destinations import (
    OutputDestinationFactory,
    JsonFileDestination,
    ExcelFileDestination,
    ConsoleDestination,
    PostgreSQLDestination
)


class TestOutputDestinationFactory:
    """Test the output destination factory."""
    
    def test_create_json_destination(self):
        """Test creating a JSON destination."""
        dest = OutputDestinationFactory.create_destination('json', file_path='output.json')
        
        assert isinstance(dest, JsonFileDestination)
        assert dest.file_path == 'output.json'
    
    def test_create_excel_destination(self):
        """Test creating an Excel destination."""
        dest = OutputDestinationFactory.create_destination('excel', file_path='output.xlsx')
        
        assert isinstance(dest, ExcelFileDestination)
        assert dest.file_path == 'output.xlsx'
    
    def test_create_console_destination(self):
        """Test creating a console destination."""
        dest = OutputDestinationFactory.create_destination('console')
        
        assert isinstance(dest, ConsoleDestination)
    
    def test_create_postgresql_destination(self):
        """Test creating a PostgreSQL destination."""
        dest = OutputDestinationFactory.create_destination(
            'postgresql',
            connection_string='postgresql://user:pass@localhost/db',
            table='results'
        )
        
        assert isinstance(dest, PostgreSQLDestination)
        assert dest.connection_string == 'postgresql://user:pass@localhost/db'
        assert dest.table == 'results'
    
    def test_create_unknown_destination_type(self):
        """Test creating an unknown destination type raises error."""
        with pytest.raises(ValueError, match="Unsupported output destination type"):
            OutputDestinationFactory.create_destination('unknown_type')
    
    def test_get_available_destinations(self):
        """Test getting list of available destination types."""
        destinations = OutputDestinationFactory.get_available_destinations()
        
        assert 'json' in destinations
        assert 'excel' in destinations
        assert 'console' in destinations
        assert 'postgresql' in destinations


class TestJsonFileDestination:
    """Test JSON output destination."""
    
    def test_json_destination_creation(self):
        """Test creating a JSON destination."""
        dest = JsonFileDestination('output.json', pretty_print=True)
        
        assert dest.file_path == 'output.json'
        assert dest.pretty_print is True
    
    def test_write_results_success(self):
        """Test successfully writing results to JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            dest = JsonFileDestination(temp_file, pretty_print=True)
            results = [
                {'question': 'Test question?', 'response': 'Test response'},
                {'question': 'Another question?', 'response': 'Another response'}
            ]
            metadata = {'total_questions': 2, 'endpoint': 'https://test.example.com'}
            
            success = dest.write_results(results, metadata)
            
            assert success is True
            
            # Verify file contents
            with open(temp_file, 'r') as f:
                data = json.load(f)
            
            assert 'timestamp' in data
            assert data['total_results'] == 2
            assert data['results'] == results
            assert data['metadata'] == metadata
            
        finally:
            os.unlink(temp_file)
    
    def test_write_results_file_error(self):
        """Test handling file write errors."""
        dest = JsonFileDestination('/invalid/path/output.json')
        results = [{'question': 'Test?', 'response': 'Test'}]
        
        success = dest.write_results(results)
        
        assert success is False
    
    def test_get_destination_info(self):
        """Test getting destination information."""
        dest = JsonFileDestination('output.json', pretty_print=True)
        info = dest.get_destination_info()
        
        assert info['type'] == 'json_file'
        assert info['file_path'] == 'output.json'
        assert info['pretty_print'] is True


class TestExcelFileDestination:
    """Test Excel output destination."""
    
    def test_excel_destination_creation(self):
        """Test creating an Excel destination."""
        dest = ExcelFileDestination('output.xlsx')
        
        assert dest.file_path == 'output.xlsx'
    
    @patch('pandas.DataFrame.to_excel')
    def test_write_results_success(self, mock_to_excel):
        """Test successfully writing results to Excel file."""
        dest = ExcelFileDestination('output.xlsx')
        results = [
            {'question': 'Test question?', 'response': 'Test response'},
            {'question': 'Another question?', 'response': 'Another response'}
        ]
        
        success = dest.write_results(results)
        
        assert success is True
        mock_to_excel.assert_called_once()
    
    @patch('pandas.DataFrame.to_excel', side_effect=Exception("Excel error"))
    def test_write_results_excel_error(self, mock_to_excel):
        """Test handling Excel write errors."""
        dest = ExcelFileDestination('output.xlsx')
        results = [{'question': 'Test?', 'response': 'Test'}]
        
        success = dest.write_results(results)
        
        assert success is False
    
    def test_get_destination_info(self):
        """Test getting destination information."""
        dest = ExcelFileDestination('output.xlsx')
        info = dest.get_destination_info()
        
        assert info['type'] == 'excel_file'
        assert info['file_path'] == 'output.xlsx'


class TestConsoleDestination:
    """Test console output destination."""
    
    def test_console_destination_creation(self):
        """Test creating a console destination."""
        dest = ConsoleDestination(format_type='json', detailed=True)
        
        assert dest.format_type == 'json'
        assert dest.detailed is True
    
    @patch('builtins.print')
    def test_write_results_json_format(self, mock_print):
        """Test writing results to console in JSON format."""
        dest = ConsoleDestination(format_type='json')
        results = [{'question': 'Test?', 'response': 'Test'}]
        metadata = {'total_questions': 1}
        
        success = dest.write_results(results, metadata)
        
        assert success is True
        mock_print.assert_called_once()
        
        # Verify JSON output structure
        printed_args = mock_print.call_args[0][0]
        data = json.loads(printed_args)
        assert 'timestamp' in data
        assert data['total_results'] == 1
        assert data['results'] == results
        assert data['metadata'] == metadata
    
    @patch('builtins.print', side_effect=Exception("Print error"))
    def test_write_results_print_error(self, mock_print):
        """Test handling print errors."""
        dest = ConsoleDestination()
        results = [{'question': 'Test?', 'response': 'Test'}]
        
        success = dest.write_results(results)
        
        assert success is False
    
    def test_get_destination_info(self):
        """Test getting destination information."""
        dest = ConsoleDestination(format_type='json', detailed=True)
        info = dest.get_destination_info()
        
        assert info['type'] == 'console_output'
        assert info['format_type'] == 'json'
        assert info['detailed'] is True


class TestPostgreSQLDestination:
    """Test PostgreSQL output destination."""
    
    def test_postgresql_destination_creation(self):
        """Test creating a PostgreSQL destination."""
        dest = PostgreSQLDestination(
            'postgresql://user:pass@localhost/db',
            'results'
        )
        
        assert dest.connection_string == 'postgresql://user:pass@localhost/db'
        assert dest.table == 'results'
    
    def test_write_results_not_implemented(self):
        """Test that write_results is not implemented (placeholder)."""
        dest = PostgreSQLDestination(
            'postgresql://user:pass@localhost/db',
            'results'
        )
        results = [{'question': 'Test?', 'response': 'Test'}]
        
        # This should return False since it's a placeholder implementation
        success = dest.write_results(results)
        assert success is False
    
    def test_get_destination_info(self):
        """Test getting destination information."""
        dest = PostgreSQLDestination(
            'postgresql://user:pass@localhost/db',
            'results'
        )
        info = dest.get_destination_info()
        
        assert info['type'] == 'postgresql_database'
        assert info['table'] == 'results'
        assert 'description' in info