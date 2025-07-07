"""
Tests for question sources.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, mock_open

from src.core.question_sources import (
    QuestionSourceFactory, 
    YamlQuestionSource, 
    DummyQuestionSource,
    PostgreSQLQuestionSource
)


class TestQuestionSourceFactory:
    """Test the question source factory."""
    
    def test_create_yaml_source(self, temp_yaml_file):
        """Test creating a YAML question source."""
        source = QuestionSourceFactory.create_source('yaml', file_path=temp_yaml_file)
        
        assert isinstance(source, YamlQuestionSource)
        assert source.file_path == temp_yaml_file
    
    def test_create_dummy_source(self):
        """Test creating a dummy question source."""
        source = QuestionSourceFactory.create_source('dummy')
        
        assert isinstance(source, DummyQuestionSource)
    
    def test_create_dummy_source_with_custom_questions(self):
        """Test creating a dummy source with custom questions."""
        custom_questions = ["Question 1?", "Question 2?"]
        source = QuestionSourceFactory.create_source('dummy', questions=custom_questions)
        
        assert isinstance(source, DummyQuestionSource)
        assert source.questions == custom_questions
    
    def test_create_postgresql_source(self):
        """Test creating a PostgreSQL question source."""
        source = QuestionSourceFactory.create_source(
            'postgresql',
            connection_string='postgresql://user:pass@localhost/db',
            table_name='questions',
            question_column='question_text'
        )
        
        assert isinstance(source, PostgreSQLQuestionSource)
        assert source.connection_string == 'postgresql://user:pass@localhost/db'
        assert source.table_name == 'questions'
        assert source.question_column == 'question_text'
    
    def test_create_unknown_source_type(self):
        """Test creating an unknown source type raises error."""
        with pytest.raises(ValueError, match="Unsupported question source type"):
            QuestionSourceFactory.create_source('unknown_type')
    
    def test_get_available_sources(self):
        """Test getting list of available source types."""
        sources = QuestionSourceFactory.get_available_sources()
        
        assert 'yaml' in sources
        assert 'dummy' in sources
        assert 'postgresql' in sources


class TestYamlQuestionSource:
    """Test YAML question source."""
    
    def test_yaml_source_creation(self, temp_yaml_file):
        """Test creating a YAML source."""
        source = YamlQuestionSource(temp_yaml_file)
        
        assert source.file_path == temp_yaml_file
    
    def test_get_questions_success(self, temp_yaml_file):
        """Test successfully loading questions from YAML file."""
        source = YamlQuestionSource(temp_yaml_file)
        questions = source.get_questions()
        
        assert len(questions) == 3
        assert "What is the capital of France?" in questions
        assert "How do you reverse a string in Python?" in questions
        assert "What is machine learning?" in questions
    
    def test_get_questions_file_not_found(self):
        """Test handling missing YAML file."""
        with pytest.raises(FileNotFoundError, match="Questions file not found"):
            YamlQuestionSource('nonexistent.yml')
    
    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', mock_open(read_data='invalid: yaml: content: ['))
    def test_get_questions_invalid_yaml(self, mock_exists):
        """Test handling invalid YAML content."""
        source = YamlQuestionSource('invalid.yml')
        with pytest.raises(ValueError, match="Error parsing YAML file"):
            source.get_questions()
    
    def test_get_source_info(self, temp_yaml_file):
        """Test getting source information."""
        source = YamlQuestionSource(temp_yaml_file)
        info = source.get_source_info()
        
        assert info['type'] == 'yaml_file'
        assert info['file_path'] == temp_yaml_file
        assert info['exists'] is True


class TestDummyQuestionSource:
    """Test dummy question source."""
    
    def test_dummy_source_default_questions(self):
        """Test dummy source with default questions."""
        source = DummyQuestionSource()
        questions = source.get_questions()
        
        assert len(questions) > 0
        assert all(isinstance(q, str) for q in questions)
        # Check that we have the expected default questions
        assert len(questions) == 5
    
    def test_dummy_source_custom_questions(self):
        """Test dummy source with custom questions."""
        custom_questions = ["Custom question 1?", "Custom question 2?"]
        source = DummyQuestionSource(custom_questions)
        questions = source.get_questions()
        
        assert questions == custom_questions
    
    def test_get_questions_returns_copy(self):
        """Test that get_questions returns a copy, not the original list."""
        source = DummyQuestionSource(["Question 1?"])
        questions1 = source.get_questions()
        questions2 = source.get_questions()
        
        questions1.append("Modified")
        assert len(questions2) == 1  # Original remains unchanged
    
    def test_get_source_info(self):
        """Test getting source information."""
        source = DummyQuestionSource(["Q1?", "Q2?"])
        info = source.get_source_info()
        
        assert info['type'] == 'dummy_static'
        assert info['question_count'] == 2
        assert 'description' in info


class TestPostgreSQLQuestionSource:
    """Test PostgreSQL question source."""
    
    def test_postgresql_source_creation(self):
        """Test creating a PostgreSQL source."""
        source = PostgreSQLQuestionSource(
            'postgresql://user:pass@localhost/db',
            'questions',
            'question_text'
        )
        
        assert source.connection_string == 'postgresql://user:pass@localhost/db'
        assert source.table_name == 'questions'
        assert source.question_column == 'question_text'
    
    def test_get_questions_placeholder(self):
        """Test that get_questions returns placeholder data."""
        source = PostgreSQLQuestionSource(
            'postgresql://user:pass@localhost/db',
            'questions',
            'question_text'
        )
        
        # This should return placeholder questions since it's a stub implementation
        questions = source.get_questions()
        assert len(questions) == 3
        assert all(isinstance(q, str) for q in questions)
    
    def test_get_source_info(self):
        """Test getting source information."""
        source = PostgreSQLQuestionSource(
            'postgresql://user:pass@localhost/db',
            'questions', 
            'question_text'
        )
        info = source.get_source_info()
        
        assert info['type'] == 'postgresql'
        assert info['table_name'] == 'questions'
        assert info['question_column'] == 'question_text'
        assert info['connection_configured'] is True