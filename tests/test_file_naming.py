"""
Tests for file naming utilities.
"""

import pytest
from datetime import datetime
from unittest.mock import patch

from src.utils.file_naming import SmartFileNamer


class TestExtractDomainFromUrl:
    """Test domain extraction from URLs."""
    
    def test_extract_domain_simple(self):
        """Test extracting domain from simple URL."""
        domain = SmartFileNamer.sanitize_domain('https://example.com')
        assert domain == 'example_com'
    
    def test_extract_domain_with_subdomain(self):
        """Test extracting domain with subdomain."""
        domain = SmartFileNamer.sanitize_domain('https://api.example.com')
        assert domain == 'api_example_com'
    
    def test_extract_domain_with_path(self):
        """Test extracting domain with path."""
        domain = SmartFileNamer.sanitize_domain('https://example.com/api/v1/test')
        assert domain == 'example_com'
    
    def test_extract_domain_with_port(self):
        """Test extracting domain with port."""
        domain = SmartFileNamer.sanitize_domain('https://example.com:8080')
        assert domain == 'example_com_8080'
    
    def test_extract_domain_with_query_params(self):
        """Test extracting domain with query parameters."""
        domain = SmartFileNamer.sanitize_domain('https://example.com/search?q=test&limit=10')
        assert domain == 'example_com'
    
    def test_extract_domain_complex(self):
        """Test extracting domain from complex URL."""
        domain = SmartFileNamer.sanitize_domain('https://test-api.my-company.co.uk:9443/api/v2')
        assert domain == 'test_api_my_company_co_uk_9443'
    
    def test_extract_domain_invalid_url(self):
        """Test extracting domain from invalid URL."""
        domain = SmartFileNamer.sanitize_domain('not-a-url')
        assert domain == 'unknown_domain'
    
    def test_extract_domain_empty_url(self):
        """Test extracting domain from empty URL."""
        domain = SmartFileNamer.sanitize_domain('')
        assert domain == 'unknown_domain'


class TestFormatTimestamp:
    """Test timestamp formatting."""
    
    @patch('src.utils.file_naming.datetime')
    def test_generate_timestamp_datetime(self, mock_datetime):
        """Test formatting timestamp as datetime."""
        mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 30, 22)
        
        timestamp = SmartFileNamer.generate_timestamp('datetime')
        assert timestamp == '2024-01-15_143022'
    
    @patch('src.utils.file_naming.datetime')
    def test_generate_timestamp_date(self, mock_datetime):
        """Test formatting timestamp as date only."""
        mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 30, 22)
        
        timestamp = SmartFileNamer.generate_timestamp('date')
        assert timestamp == '2024-01-15'
    
    @patch('src.utils.file_naming.datetime')
    def test_generate_timestamp_time(self, mock_datetime):
        """Test formatting timestamp as time only."""
        mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 30, 22)
        
        timestamp = SmartFileNamer.generate_timestamp('time')
        assert timestamp == '143022'
    
    @patch('src.utils.file_naming.datetime')
    def test_generate_timestamp_unix(self, mock_datetime):
        """Test formatting timestamp as unix timestamp."""
        mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 30, 22)
        mock_datetime.now().timestamp.return_value = 1705330222.0
        
        timestamp = SmartFileNamer.generate_timestamp('unix')
        assert timestamp == '1705330222'
    
    def test_generate_timestamp_invalid_format(self):
        """Test formatting timestamp with invalid format."""
        timestamp = SmartFileNamer.generate_timestamp('invalid')
        # Should fallback to datetime format
        assert len(timestamp) > 0
        assert '_' in timestamp  # datetime format contains underscore


class TestGenerateUniqueFilename:
    """Test unique filename generation."""
    
    @patch('src.utils.file_naming.datetime')
    def test_generate_filename_with_domain_and_timestamp(self, mock_datetime):
        """Test generating filename with domain and timestamp."""
        mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 30, 22)
        
        filename = SmartFileNamer.generate_unique_filename(
            'https://api.example.com',
            template='results',
            file_extension='json',
            include_timestamp=True
        )
        
        assert filename == 'results_api_example_com_2024-01-15_143022.json'
    
    @patch('src.utils.file_naming.datetime')
    def test_generate_filename_domain_only(self, mock_datetime):
        """Test generating filename with domain only."""
        filename = SmartFileNamer.generate_unique_filename(
            'https://test.example.com',
            template='output',
            file_extension='xlsx',
            include_timestamp=False
        )
        
        assert filename == 'output_test_example_com.xlsx'
    
    @patch('src.utils.file_naming.datetime')
    def test_generate_filename_timestamp_only(self, mock_datetime):
        """Test generating filename with timestamp only."""
        mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 30, 22)
        
        filename = SmartFileNamer.generate_unique_filename(
            'https://example.com',
            template='test',
            file_extension='json',
            include_domain=False,
            include_timestamp=True
        )
        
        assert filename == 'test_2024-01-15_143022.json'
    
    def test_generate_filename_template_only(self):
        """Test generating filename with template only."""
        filename = SmartFileNamer.generate_unique_filename(
            'https://example.com',
            template='simple',
            file_extension='txt',
            include_domain=False,
            include_timestamp=False
        )
        
        assert filename == 'simple.txt'
    
    @patch('src.utils.file_naming.datetime')
    def test_generate_filename_custom_timestamp_format(self, mock_datetime):
        """Test generating filename with custom timestamp format."""
        mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 30, 22)
        
        filename = SmartFileNamer.generate_unique_filename(
            'https://example.com',
            template='daily',
            file_extension='json',
            include_domain=False,
            include_timestamp=True,
            timestamp_format='date'
        )
        
        assert filename == 'daily_2024-01-15.json'
    
    def test_generate_filename_no_template(self):
        """Test generating filename without template."""
        filename = SmartFileNamer.generate_unique_filename(
            'https://api.example.com',
            file_extension='json',
            include_domain=True,
            include_timestamp=False
        )
        
        assert filename == 'api_example_com.json'
    
    def test_generate_filename_no_extension(self):
        """Test generating filename without extension."""
        filename = SmartFileNamer.generate_unique_filename(
            'https://example.com',
            template='test',
            include_domain=False,
            include_timestamp=False
        )
        
        assert filename == 'test'
    
    @patch('src.utils.file_naming.datetime')
    def test_generate_filename_all_options(self, mock_datetime):
        """Test generating filename with all options enabled."""
        mock_datetime.now.return_value = datetime(2024, 1, 15, 14, 30, 22)
        
        filename = SmartFileNamer.generate_unique_filename(
            'https://test-api.my-company.com:8080/api',
            template='endpoint_test',
            file_extension='xlsx',
            include_domain=True,
            include_timestamp=True,
            timestamp_format='datetime'
        )
        
        expected = 'endpoint_test_test_api_my_company_com_8080_2024-01-15_143022.xlsx'
        assert filename == expected