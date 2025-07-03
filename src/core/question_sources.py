"""
Question source interfaces and implementations.

This module provides an abstraction layer for different question data sources,
allowing for easy swapping between YAML files, databases, APIs, etc.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import yaml
import os


class QuestionSource(ABC):
    """Abstract base class for question data sources."""
    
    @abstractmethod
    def get_questions(self) -> List[str]:
        """
        Retrieve a list of questions from the data source.
        
        Returns:
            List[str]: A list of question strings.
        """
        pass
    
    @abstractmethod
    def get_source_info(self) -> Dict[str, Any]:
        """
        Get information about the data source.
        
        Returns:
            Dict[str, Any]: Metadata about the source (type, location, etc.)
        """
        pass


class YamlQuestionSource(QuestionSource):
    """Question source that reads from YAML files."""
    
    def __init__(self, file_path: str):
        """
        Initialize with a YAML file path.
        
        Args:
            file_path (str): Path to the YAML file containing questions.
        """
        self.file_path = file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Questions file not found: {file_path}")
    
    def get_questions(self) -> List[str]:
        """Read questions from the YAML file."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                data = yaml.safe_load(file)
                
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'questions' in data:
                return data['questions']
            else:
                raise ValueError(f"Invalid YAML structure in {self.file_path}")
                
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file {self.file_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error reading questions from {self.file_path}: {e}")
    
    def get_source_info(self) -> Dict[str, Any]:
        """Get information about the YAML file source."""
        return {
            'type': 'yaml_file',
            'file_path': self.file_path,
            'exists': os.path.exists(self.file_path),
            'size': os.path.getsize(self.file_path) if os.path.exists(self.file_path) else 0
        }


class DummyQuestionSource(QuestionSource):
    """Dummy question source with static questions for testing."""
    
    def __init__(self, questions: List[str] = None):
        """
        Initialize with optional custom questions.
        
        Args:
            questions (List[str], optional): Custom list of questions. 
                                           If None, uses default test questions.
        """
        self.questions = questions or [
            "What is the capital of France?",
            "How do you reverse a string in Python?",
            "What are the main principles of object-oriented programming?",
            "Explain the difference between HTTP and HTTPS.",
            "What is the purpose of a database index?"
        ]
    
    def get_questions(self) -> List[str]:
        """Return the static list of questions."""
        return self.questions.copy()
    
    def get_source_info(self) -> Dict[str, Any]:
        """Get information about the dummy source."""
        return {
            'type': 'dummy_static',
            'question_count': len(self.questions),
            'description': 'Static in-memory question source for testing'
        }


class PostgreSQLQuestionSource(QuestionSource):
    """PostgreSQL database question source (placeholder implementation)."""
    
    def __init__(self, connection_string: str, table_name: str = 'questions', 
                 question_column: str = 'question_text'):
        """
        Initialize PostgreSQL question source.
        
        Args:
            connection_string (str): PostgreSQL connection string
            table_name (str): Name of the table containing questions
            question_column (str): Name of the column containing question text
        """
        self.connection_string = connection_string
        self.table_name = table_name
        self.question_column = question_column
        
        # TODO: Add actual PostgreSQL connection logic
        # import psycopg2
        # self.connection = psycopg2.connect(connection_string)
    
    def get_questions(self) -> List[str]:
        """
        Retrieve questions from PostgreSQL database.
        
        Note: This is a placeholder implementation.
        In a real implementation, this would execute a SQL query.
        """
        # TODO: Implement actual database query
        # cursor = self.connection.cursor()
        # cursor.execute(f"SELECT {self.question_column} FROM {self.table_name}")
        # questions = [row[0] for row in cursor.fetchall()]
        # cursor.close()
        # return questions
        
        # Placeholder return for now
        return [
            "Sample question from PostgreSQL database",
            "Another database question",
            "PostgreSQL integration test question"
        ]
    
    def get_source_info(self) -> Dict[str, Any]:
        """Get information about the PostgreSQL source."""
        return {
            'type': 'postgresql',
            'table_name': self.table_name,
            'question_column': self.question_column,
            'connection_configured': bool(self.connection_string),
            'status': 'placeholder_implementation'
        }


class QuestionSourceFactory:
    """Factory class for creating question source instances."""
    
    @staticmethod
    def create_source(source_type: str, **kwargs) -> QuestionSource:
        """
        Create a question source instance based on the specified type.
        
        Args:
            source_type (str): Type of source ('yaml', 'dummy', 'postgresql')
            **kwargs: Additional arguments specific to each source type
            
        Returns:
            QuestionSource: An instance of the appropriate question source
            
        Raises:
            ValueError: If source_type is not supported
        """
        if source_type.lower() == 'yaml':
            file_path = kwargs.get('file_path', './questions.yml')
            return YamlQuestionSource(file_path)
        
        elif source_type.lower() == 'dummy':
            questions = kwargs.get('questions')
            return DummyQuestionSource(questions)
        
        elif source_type.lower() == 'postgresql':
            connection_string = kwargs.get('connection_string')
            table_name = kwargs.get('table_name', 'questions')
            question_column = kwargs.get('question_column', 'question_text')
            return PostgreSQLQuestionSource(connection_string, table_name, question_column)
        
        else:
            raise ValueError(f"Unsupported question source type: {source_type}")
    
    @staticmethod
    def get_available_sources() -> List[str]:
        """Get a list of available question source types."""
        return ['yaml', 'dummy', 'postgresql']