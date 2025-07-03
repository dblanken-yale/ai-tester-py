"""File naming utilities for AI Tester."""
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional


class SmartFileNamer:
    """Generate unique file names with domain and timestamp identifiers."""
    
    @staticmethod
    def sanitize_domain(url: str) -> str:
        """
        Extract and sanitize domain name from URL for use in filenames.
        
        Args:
            url: The URL to extract domain from
            
        Returns:
            Sanitized domain name suitable for filenames
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove common prefixes
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Replace dots and special characters with underscores
            domain = re.sub(r'[^\w\-]', '_', domain)
            
            # Remove consecutive underscores
            domain = re.sub(r'_+', '_', domain)
            
            # Remove leading/trailing underscores
            domain = domain.strip('_')
            
            return domain if domain else 'unknown_domain'
            
        except Exception:
            return 'unknown_domain'
    
    @staticmethod
    def generate_timestamp(format_type: str = 'datetime') -> str:
        """
        Generate timestamp string for file naming.
        
        Args:
            format_type: Type of timestamp format
                - 'datetime': Full datetime (2024-01-15_143022)
                - 'date': Date only (2024-01-15)
                - 'time': Time only (143022)
                - 'unix': Unix timestamp (1705329022)
                
        Returns:
            Formatted timestamp string
        """
        now = datetime.now()
        
        if format_type == 'datetime':
            return now.strftime('%Y-%m-%d_%H%M%S')
        elif format_type == 'date':
            return now.strftime('%Y-%m-%d')
        elif format_type == 'time':
            return now.strftime('%H%M%S')
        elif format_type == 'unix':
            return str(int(time.time()))
        else:
            return now.strftime('%Y-%m-%d_%H%M%S')
    
    @staticmethod
    def generate_unique_filename(
        base_url: str,
        template: Optional[str] = None,
        file_extension: str = 'json',
        include_timestamp: bool = True,
        timestamp_format: str = 'datetime'
    ) -> str:
        """
        Generate unique filename with domain and timestamp.
        
        Args:
            base_url: The URL being tested
            template: Template name (e.g., 'results', 'errors')
            file_extension: File extension without dot
            include_timestamp: Whether to include timestamp
            timestamp_format: Format for timestamp
            
        Returns:
            Generated filename
            
        Examples:
            generate_unique_filename('https://api.example.com', 'results')
            -> 'results_api_example_com_2024-01-15_143022.json'
            
            generate_unique_filename('https://test.ai.com', 'errors', 'xlsx', False)
            -> 'errors_test_ai_com.xlsx'
        """
        domain = SmartFileNamer.sanitize_domain(base_url)
        
        # Build filename parts
        parts = []
        
        if template:
            parts.append(template)
        
        parts.append(domain)
        
        if include_timestamp:
            timestamp = SmartFileNamer.generate_timestamp(timestamp_format)
            parts.append(timestamp)
        
        # Join parts and add extension
        filename = '_'.join(parts)
        return f"{filename}.{file_extension}"
    
    @staticmethod
    def generate_output_path(
        base_url: str,
        base_template: Optional[str] = None,
        file_extension: str = 'json',
        output_dir: Optional[str] = None,
        include_timestamp: bool = True
    ) -> str:
        """
        Generate complete output file path.
        
        Args:
            base_url: The URL being tested
            base_template: Base template for filename
            file_extension: File extension
            output_dir: Output directory (optional)
            include_timestamp: Whether to include timestamp
            
        Returns:
            Complete file path
        """
        filename = SmartFileNamer.generate_unique_filename(
            base_url=base_url,
            template=base_template,
            file_extension=file_extension,
            include_timestamp=include_timestamp
        )
        
        if output_dir:
            path = Path(output_dir) / filename
            # Ensure output directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            return str(path)
        
        return filename
    
    @staticmethod
    def parse_template_variables(template: str, base_url: str) -> str:
        """
        Parse template variables in filename template.
        
        Supported variables:
        - {domain}: Sanitized domain name
        - {timestamp}: Current timestamp
        - {date}: Current date
        - {time}: Current time
        
        Args:
            template: Template string with variables
            base_url: URL for domain extraction
            
        Returns:
            Template with variables replaced
            
        Example:
            parse_template_variables('results_{domain}_{date}', 'https://api.example.com')
            -> 'results_api_example_com_2024-01-15'
        """
        domain = SmartFileNamer.sanitize_domain(base_url)
        
        replacements = {
            '{domain}': domain,
            '{timestamp}': SmartFileNamer.generate_timestamp('datetime'),
            '{date}': SmartFileNamer.generate_timestamp('date'),
            '{time}': SmartFileNamer.generate_timestamp('time'),
            '{unix}': SmartFileNamer.generate_timestamp('unix')
        }
        
        result = template
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)
        
        return result