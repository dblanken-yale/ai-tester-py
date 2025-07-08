"""
Output destination interfaces and implementations.

This module provides an abstraction layer for different output destinations,
allowing for easy swapping between files, databases, APIs, etc.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
import pandas as pd
import io
import sys
import os
import logging
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.styles import Alignment

logger = logging.getLogger(__name__)


class OutputDestination(ABC):
    """Abstract base class for output destinations."""
    
    @abstractmethod
    def write_results(self, results: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Write results to the destination.
        
        Args:
            results (List[Dict[str, Any]]): List of result dictionaries
            metadata (Optional[Dict[str, Any]]): Additional metadata about the run
            
        Returns:
            bool: True if write was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_destination_info(self) -> Dict[str, Any]:
        """
        Get information about the destination.
        
        Returns:
            Dict[str, Any]: Metadata about the destination (type, location, etc.)
        """
        pass


class JsonFileDestination(OutputDestination):
    """Output destination that writes to JSON files."""
    
    def __init__(self, file_path: str, pretty_print: bool = True):
        """
        Initialize with a JSON file path.
        
        Args:
            file_path (str): Path to the JSON output file
            pretty_print (bool): Whether to format JSON with indentation
        """
        self.file_path = file_path
        self.pretty_print = pretty_print
    
    def write_results(self, results: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Write results to JSON file."""
        try:
            output_data = {
                'timestamp': datetime.now().isoformat(),
                'total_results': len(results),
                'results': results
            }
            
            if metadata:
                output_data['metadata'] = metadata
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                if self.pretty_print:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(output_data, f, ensure_ascii=False)
            
            logger.info(f"Successfully wrote {len(results)} results to JSON file: {self.file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write results to JSON file {self.file_path}: {e}")
            return False
    
    def get_destination_info(self) -> Dict[str, Any]:
        """Get information about the JSON file destination."""
        return {
            'type': 'json_file',
            'file_path': self.file_path,
            'pretty_print': self.pretty_print,
            'exists': os.path.exists(self.file_path),
            'size': os.path.getsize(self.file_path) if os.path.exists(self.file_path) else 0
        }


class ExcelFileDestination(OutputDestination):
    """Output destination that writes to Excel files."""
    
    def __init__(self, file_path: str, sheet_name: str = 'Results'):
        """
        Initialize with Excel file path.
        
        Args:
            file_path (str): Path to the Excel output file
            sheet_name (str): Name of the worksheet
        """
        self.file_path = file_path
        self.sheet_name = sheet_name
    
    def write_results(self, results: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Write results to Excel file."""
        try:
            if not results:
                logger.warning("No results to write to Excel file")
                return True
            
            # Create DataFrame from results
            df = pd.DataFrame(results)
            
            # Handle citations column if present
            if 'citations' in df.columns:
                citations = pd.DataFrame(df['citations'].tolist()).fillna('')
                df = df.drop('citations', axis=1)
                df = pd.concat([df[['question', 'answer']], citations], axis=1)
                df.columns = ['Question', 'Answer'] + [f'Cite {i+1}' for i in range(citations.shape[1])]
            else:
                # Basic question/answer columns
                if 'question' in df.columns and 'answer' in df.columns:
                    df = df[['question', 'answer']]
                    df.columns = ['Question', 'Answer']
            
            # Write to Excel
            with pd.ExcelWriter(self.file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=self.sheet_name, index=False)
                
                # Add metadata sheet if provided
                if metadata:
                    metadata_df = pd.DataFrame(list(metadata.items()), columns=['Key', 'Value'])
                    metadata_df.to_excel(writer, sheet_name='Metadata', index=False)
            
            # Apply formatting
            self._format_excel_file()
            
            logger.info(f"Successfully wrote {len(results)} results to Excel file: {self.file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write results to Excel file {self.file_path}: {e}")
            return False
    
    def _format_excel_file(self):
        """Apply formatting to the Excel file."""
        try:
            workbook = load_workbook(self.file_path)
            sheet = workbook[self.sheet_name]
            
            # Set column widths and alignment
            sheet.column_dimensions['A'].width = 140  # Question column
            sheet.column_dimensions['B'].width = 30   # Answer column
            
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.column_letter in ['A', 'B']:
                        cell.alignment = Alignment(vertical='top', wrap_text=True)
                        sheet.row_dimensions[cell.row].height = None
                    else:
                        cell.alignment = Alignment(vertical='top')
            
            workbook.save(self.file_path)
            
        except Exception as e:
            logger.warning(f"Failed to format Excel file: {e}")
    
    def get_destination_info(self) -> Dict[str, Any]:
        """Get information about the Excel file destination."""
        return {
            'type': 'excel_file',
            'file_path': self.file_path,
            'sheet_name': self.sheet_name,
            'exists': os.path.exists(self.file_path),
            'size': os.path.getsize(self.file_path) if os.path.exists(self.file_path) else 0
        }


class PostgreSQLDestination(OutputDestination):
    """Output destination that writes to PostgreSQL database."""
    
    def __init__(self, connection_string: str, table_name: str = 'ai_results', 
                 create_table: bool = True):
        """
        Initialize PostgreSQL destination.
        
        Args:
            connection_string (str): PostgreSQL connection string
            table_name (str): Name of the table to write results
            create_table (bool): Whether to create table if it doesn't exist
        """
        self.connection_string = connection_string
        self.table_name = table_name
        self.create_table = create_table
        
        # Validate connection string is provided
        if not connection_string:
            raise ValueError("PostgreSQL connection string is required")
    
    def write_results(self, results: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Write results to PostgreSQL database.
        
        This is a stub implementation. Add actual database connection and insertion logic here.
        
        Example implementation would:
        1. Connect to PostgreSQL using psycopg2 or asyncpg
        2. Create table if create_table=True and table doesn't exist
        3. Insert each result as a row with proper data types
        4. Handle errors gracefully and log appropriately
        
        Args:
            results: List of result dictionaries to insert
            metadata: Optional metadata about the test run
            
        Returns:
            bool: True if write was successful, False otherwise
        """
        try:
            # TODO: Implement actual PostgreSQL connection and insertion
            # This stub logs what would be written for development/testing
            
            logger.info(f"PostgreSQL stub: would write {len(results)} results to table '{self.table_name}'")
            logger.info(f"Connection string configured: {bool(self.connection_string)}")
            
            if metadata:
                logger.info(f"Run metadata would be included: {list(metadata.keys())}")
            
            # Log sample data structure for first result (if any)
            if results:
                sample_result = results[0]
                logger.info(f"Sample result structure: {list(sample_result.keys())}")
            
            # In a real implementation, you would:
            # - Import psycopg2 or asyncpg
            # - Connect to database
            # - Create table with appropriate schema
            # - Insert results with proper SQL
            # - Handle transactions and rollbacks
            # - Return actual success status
            
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL destination error: {e}")
            return False
    
    def get_destination_info(self) -> Dict[str, Any]:
        """Get information about the PostgreSQL destination."""
        return {
            'type': 'postgresql',
            'table_name': self.table_name,
            'create_table': self.create_table,
            'connection_configured': bool(self.connection_string),
            'status': 'stub_implementation',
            'note': 'This is a stub implementation - add actual PostgreSQL logic'
        }


class ConsoleDestination(OutputDestination):
    """Output destination that writes to console/logs."""
    
    def __init__(self, format_type: str = 'json', detailed: bool = True):
        """
        Initialize console destination.
        
        Args:
            format_type (str): Format for console output ('json', 'summary', 'detailed')
            detailed (bool): Whether to include full result details
        """
        self.format_type = format_type
        self.detailed = detailed
    
    def write_results(self, results: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Write results to console."""
        try:
            if self.format_type == 'json':
                output_data = {
                    'timestamp': datetime.now().isoformat(),
                    'total_results': len(results),
                    'results': results
                }
                if metadata:
                    output_data['metadata'] = metadata
                
                print(json.dumps(output_data, indent=2, ensure_ascii=False))
            
            elif self.format_type == 'summary':
                print(f"\n=== AI Tester Results Summary ===")
                print(f"Timestamp: {datetime.now().isoformat()}")
                print(f"Total Results: {len(results)}")
                
                if metadata:
                    print(f"Metadata: {metadata}")
                
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. Question: {result.get('question', 'N/A')[:100]}...")
                    if result.get('answer'):
                        print(f"   Answer: {result['answer'][:100]}...")
                    if result.get('citations'):
                        print(f"   Citations: {len(result['citations'])} found")
            
            elif self.format_type == 'detailed':
                print(f"\n=== AI Tester Detailed Results ===")
                print(f"Timestamp: {datetime.now().isoformat()}")
                print(f"Total Results: {len(results)}")
                
                if metadata:
                    print(f"\nRun Metadata:")
                    for key, value in metadata.items():
                        print(f"  {key}: {value}")
                
                for i, result in enumerate(results, 1):
                    print(f"\n--- Result {i} ---")
                    print(f"Question: {result.get('question', 'N/A')}")
                    print(f"Answer: {result.get('answer', 'N/A')}")
                    
                    if result.get('citations'):
                        print(f"Citations ({len(result['citations'])}):")
                        for j, citation in enumerate(result['citations'], 1):
                            print(f"  {j}. {citation}")
                    
                    if result.get('error'):
                        print(f"Error: {result['error']}")
            
            logger.info(f"Successfully output {len(results)} results to console")
            return True
            
        except Exception as e:
            logger.error(f"Failed to write results to console: {e}")
            return False
    
    def get_destination_info(self) -> Dict[str, Any]:
        """Get information about the console destination."""
        return {
            'type': 'console',
            'format_type': self.format_type,
            'detailed': self.detailed
        }


class OutputDestinationFactory:
    """Factory class for creating output destination instances."""
    
    @staticmethod
    def create_destination(destination_type: str, **kwargs) -> OutputDestination:
        """
        Create an output destination instance based on the specified type.
        
        Args:
            destination_type (str): Type of destination ('json', 'excel', 'postgresql', 'console')
            **kwargs: Additional arguments specific to each destination type
            
        Returns:
            OutputDestination: An instance of the appropriate output destination
            
        Raises:
            ValueError: If destination_type is not supported
        """
        destination_type = destination_type.lower()
        
        if destination_type == 'json':
            file_path = kwargs.get('file_path', './results.json')
            pretty_print = kwargs.get('pretty_print', True)
            return JsonFileDestination(file_path, pretty_print)
        
        elif destination_type == 'excel':
            file_path = kwargs.get('file_path', './results.xlsx')
            sheet_name = kwargs.get('sheet_name', 'Results')
            return ExcelFileDestination(file_path, sheet_name)
        
        elif destination_type == 'postgresql':
            connection_string = kwargs.get('connection_string')
            table_name = kwargs.get('table_name', 'ai_results')
            create_table = kwargs.get('create_table', True)
            return PostgreSQLDestination(connection_string, table_name, create_table)
        
        elif destination_type == 'console':
            format_type = kwargs.get('format_type', 'json')
            detailed = kwargs.get('detailed', True)
            return ConsoleDestination(format_type, detailed)
        
        else:
            raise ValueError(f"Unsupported output destination type: {destination_type}")
    
    @staticmethod
    def get_available_destinations() -> List[str]:
        """Get a list of available output destination types."""
        return ['json', 'excel', 'postgresql', 'console']