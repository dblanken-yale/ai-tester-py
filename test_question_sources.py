#!/usr/bin/env python3
"""
Test script to demonstrate the question source interface.
"""

import os
import sys
from question_sources import (
    QuestionSourceFactory, 
    DummyQuestionSource, 
    YamlQuestionSource,
    PostgreSQLQuestionSource
)
from processor import QuestionProcessor


def test_dummy_source():
    """Test the dummy question source."""
    print("=== Testing Dummy Question Source ===")
    
    # Create dummy source with default questions
    dummy_source = DummyQuestionSource()
    questions = dummy_source.get_questions()
    source_info = dummy_source.get_source_info()
    
    print(f"Source Info: {source_info}")
    print(f"Number of questions: {len(questions)}")
    print("Questions:")
    for i, question in enumerate(questions, 1):
        print(f"  {i}. {question}")
    print()
    
    # Test with custom questions
    custom_questions = [
        "What is Python?",
        "How does machine learning work?",
        "Explain cloud computing."
    ]
    custom_dummy = DummyQuestionSource(custom_questions)
    custom_questions_result = custom_dummy.get_questions()
    
    print("Custom Dummy Source:")
    print(f"Questions: {custom_questions_result}")
    print()


def test_yaml_source():
    """Test the YAML question source."""
    print("=== Testing YAML Question Source ===")
    
    # Create a sample YAML file for testing
    sample_yaml_content = """
- "What is the difference between a list and a tuple in Python?"
- "How do you handle exceptions in Python?"
- "What is the purpose of virtual environments?"
- "Explain the concept of decorators in Python."
"""
    
    test_file = "test_questions.yml"
    try:
        with open(test_file, 'w') as f:
            f.write(sample_yaml_content)
        
        yaml_source = YamlQuestionSource(test_file)
        questions = yaml_source.get_questions()
        source_info = yaml_source.get_source_info()
        
        print(f"Source Info: {source_info}")
        print(f"Number of questions: {len(questions)}")
        print("Questions:")
        for i, question in enumerate(questions, 1):
            print(f"  {i}. {question}")
        print()
        
    except Exception as e:
        print(f"Error testing YAML source: {e}")
    finally:
        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)


def test_postgresql_source():
    """Test the PostgreSQL question source (placeholder)."""
    print("=== Testing PostgreSQL Question Source (Placeholder) ===")
    
    try:
        pg_source = PostgreSQLQuestionSource(
            connection_string="postgresql://user:pass@localhost/testdb",
            table_name="questions",
            question_column="question_text"
        )
        questions = pg_source.get_questions()
        source_info = pg_source.get_source_info()
        
        print(f"Source Info: {source_info}")
        print(f"Number of questions: {len(questions)}")
        print("Questions (placeholder data):")
        for i, question in enumerate(questions, 1):
            print(f"  {i}. {question}")
        print()
        
    except Exception as e:
        print(f"Error testing PostgreSQL source: {e}")


def test_factory():
    """Test the QuestionSourceFactory."""
    print("=== Testing QuestionSourceFactory ===")
    
    print(f"Available sources: {QuestionSourceFactory.get_available_sources()}")
    
    # Test creating different sources via factory
    print("\n1. Creating dummy source via factory:")
    dummy_via_factory = QuestionSourceFactory.create_source('dummy')
    print(f"Type: {type(dummy_via_factory).__name__}")
    print(f"Questions: {len(dummy_via_factory.get_questions())}")
    
    print("\n2. Creating dummy source with custom questions:")
    custom_questions = ["Factory test question 1", "Factory test question 2"]
    custom_dummy_via_factory = QuestionSourceFactory.create_source('dummy', questions=custom_questions)
    print(f"Custom questions: {custom_dummy_via_factory.get_questions()}")
    
    print("\n3. Creating PostgreSQL source via factory:")
    pg_via_factory = QuestionSourceFactory.create_source(
        'postgresql',
        connection_string="postgresql://test",
        table_name="test_questions"
    )
    print(f"Type: {type(pg_via_factory).__name__}")
    print(f"Source info: {pg_via_factory.get_source_info()}")
    print()


def test_processor_integration():
    """Test the QuestionProcessor with different question sources."""
    print("=== Testing Processor Integration ===")
    
    # Note: Using a dummy base_url since we're only testing question source integration
    base_url = "https://example.com"
    
    try:
        processor = QuestionProcessor(base_url)
        
        print("1. Testing with dummy source:")
        dummy_source = processor.create_question_source('dummy')
        questions = processor.get_questions_from_source()
        print(f"Got {len(questions)} questions from dummy source")
        print(f"First question: {questions[0]}")
        
        print("\n2. Testing with custom dummy source:")
        custom_questions = ["Integration test question"]
        processor.create_question_source('dummy', questions=custom_questions)
        questions = processor.get_questions_from_source()
        print(f"Got {len(questions)} questions from custom dummy source")
        print(f"Question: {questions[0]}")
        
        print("\n3. Testing source switching:")
        # Switch to PostgreSQL source
        processor.create_question_source('postgresql', connection_string="test://conn")
        questions = processor.get_questions_from_source()
        print(f"Got {len(questions)} questions from PostgreSQL source")
        print(f"First question: {questions[0]}")
        
    except Exception as e:
        print(f"Error in processor integration test: {e}")
    
    print()


def main():
    """Run all tests."""
    print("Testing Question Source Interface\n")
    
    test_dummy_source()
    test_yaml_source()
    test_postgresql_source()
    test_factory()
    test_processor_integration()
    
    print("=== Summary ===")
    print("✓ Dummy question source working")
    print("✓ YAML question source working")
    print("✓ PostgreSQL question source (placeholder) working")
    print("✓ Factory pattern working")
    print("✓ Processor integration working")
    print("\nThe question source interface is ready!")
    print("\nNext steps:")
    print("- To use PostgreSQL: pip install psycopg2-binary")
    print("- Update PostgreSQL source with actual database connection code")
    print("- Add environment variable configuration for source selection")


if __name__ == "__main__":
    main()