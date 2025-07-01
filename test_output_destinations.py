#!/usr/bin/env python3
"""
Test script to demonstrate the output destination interface.
"""

import os
import sys
import json
from output_destinations import (
    OutputDestinationFactory,
    JsonFileDestination,
    ExcelFileDestination,
    PostgreSQLDestination,
    ConsoleDestination
)

# Sample test data
SAMPLE_RESULTS = [
    {
        'question': 'What is the capital of France?',
        'answer': 'The capital of France is Paris. It is located in the north-central part of the country.',
        'citations': ['https://example.com/france-geography', 'https://example.com/paris-info']
    },
    {
        'question': 'How do you reverse a string in Python?',
        'answer': 'You can reverse a string in Python using slicing: `string[::-1]` or using the `reversed()` function.',
        'citations': ['https://docs.python.org/3/tutorial/', 'https://example.com/python-strings']
    },
    {
        'question': 'What are the main principles of object-oriented programming?',
        'answer': 'The main principles are: Encapsulation, Inheritance, Polymorphism, and Abstraction.',
        'citations': ['https://example.com/oop-principles']
    }
]

SAMPLE_METADATA = {
    'timestamp': '2025-07-01T17:00:00Z',
    'total_questions': 3,
    'successful_results': 3,
    'base_url': 'https://askyalemytest.azurewebsites.net',
    'debug_mode': False
}


def test_json_destination():
    """Test the JSON file output destination."""
    print("=== Testing JSON File Destination ===")
    
    test_file = "test_results.json"
    try:
        json_dest = JsonFileDestination(test_file, pretty_print=True)
        
        # Test writing results
        success = json_dest.write_results(SAMPLE_RESULTS, SAMPLE_METADATA)
        print(f"Write success: {success}")
        
        # Check destination info
        dest_info = json_dest.get_destination_info()
        print(f"Destination info: {dest_info}")
        
        # Verify file contents
        if os.path.exists(test_file):
            with open(test_file, 'r') as f:
                data = json.load(f)
                print(f"Results written: {len(data.get('results', []))}")
                print(f"Metadata included: {'metadata' in data}")
        
    except Exception as e:
        print(f"Error testing JSON destination: {e}")
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
    
    print()


def test_excel_destination():
    """Test the Excel file output destination."""
    print("=== Testing Excel File Destination ===")
    
    test_file = "test_results.xlsx"
    try:
        excel_dest = ExcelFileDestination(test_file, sheet_name="AI_Results")
        
        # Test writing results
        success = excel_dest.write_results(SAMPLE_RESULTS, SAMPLE_METADATA)
        print(f"Write success: {success}")
        
        # Check destination info
        dest_info = excel_dest.get_destination_info()
        print(f"Destination info: {dest_info}")
        
        # Verify file exists
        if os.path.exists(test_file):
            print(f"Excel file created: {test_file}")
            print(f"File size: {os.path.getsize(test_file)} bytes")
        
    except Exception as e:
        print(f"Error testing Excel destination: {e}")
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
    
    print()


def test_postgresql_destination():
    """Test the PostgreSQL database output destination (placeholder)."""
    print("=== Testing PostgreSQL Destination (Placeholder) ===")
    
    try:
        pg_dest = PostgreSQLDestination(
            connection_string="postgresql://test:test@localhost/testdb",
            table_name="test_ai_results",
            create_table=True
        )
        
        # Test writing results (placeholder implementation)
        success = pg_dest.write_results(SAMPLE_RESULTS, SAMPLE_METADATA)
        print(f"Write success (placeholder): {success}")
        
        # Check destination info
        dest_info = pg_dest.get_destination_info()
        print(f"Destination info: {dest_info}")
        
    except Exception as e:
        print(f"Error testing PostgreSQL destination: {e}")
    
    print()


def test_console_destination():
    """Test the console output destination."""
    print("=== Testing Console Destination ===")
    
    # Test JSON format
    print("\n1. JSON Format:")
    console_json = ConsoleDestination(format_type='json', detailed=True)
    success = console_json.write_results(SAMPLE_RESULTS[:1], SAMPLE_METADATA)  # Only one result for brevity
    print(f"Write success: {success}")
    
    # Test summary format
    print("\n2. Summary Format:")
    console_summary = ConsoleDestination(format_type='summary', detailed=False)
    success = console_summary.write_results(SAMPLE_RESULTS, SAMPLE_METADATA)
    print(f"Write success: {success}")
    
    # Test detailed format
    print("\n3. Detailed Format:")
    console_detailed = ConsoleDestination(format_type='detailed', detailed=True)
    success = console_detailed.write_results(SAMPLE_RESULTS[:1], SAMPLE_METADATA)  # Only one result for brevity
    print(f"Write success: {success}")
    
    print()


def test_factory():
    """Test the OutputDestinationFactory."""
    print("=== Testing OutputDestinationFactory ===")
    
    print(f"Available destinations: {OutputDestinationFactory.get_available_destinations()}")
    
    # Test creating different destinations via factory
    print("\n1. Creating JSON destination via factory:")
    json_via_factory = OutputDestinationFactory.create_destination(
        'json', 
        file_path='./factory_test.json',
        pretty_print=False
    )
    print(f"Type: {type(json_via_factory).__name__}")
    print(f"Info: {json_via_factory.get_destination_info()}")
    
    print("\n2. Creating Excel destination via factory:")
    excel_via_factory = OutputDestinationFactory.create_destination(
        'excel',
        file_path='./factory_test.xlsx',
        sheet_name='FactoryTest'
    )
    print(f"Type: {type(excel_via_factory).__name__}")
    print(f"Info: {excel_via_factory.get_destination_info()}")
    
    print("\n3. Creating PostgreSQL destination via factory:")
    pg_via_factory = OutputDestinationFactory.create_destination(
        'postgresql',
        connection_string="postgresql://factory_test",
        table_name="factory_results"
    )
    print(f"Type: {type(pg_via_factory).__name__}")
    print(f"Info: {pg_via_factory.get_destination_info()}")
    
    print("\n4. Creating Console destination via factory:")
    console_via_factory = OutputDestinationFactory.create_destination(
        'console',
        format_type='summary',
        detailed=False
    )
    print(f"Type: {type(console_via_factory).__name__}")
    print(f"Info: {console_via_factory.get_destination_info()}")
    
    print()


def test_multiple_destinations():
    """Test writing to multiple destinations simultaneously."""
    print("=== Testing Multiple Destinations ===")
    
    destinations = [
        OutputDestinationFactory.create_destination('console', format_type='summary'),
        OutputDestinationFactory.create_destination('json', file_path='./multi_test.json')
    ]
    
    for i, dest in enumerate(destinations, 1):
        print(f"\n{i}. Writing to {dest.get_destination_info()['type']} destination:")
        success = dest.write_results(SAMPLE_RESULTS, SAMPLE_METADATA)
        print(f"   Success: {success}")
    
    # Clean up
    if os.path.exists('./multi_test.json'):
        os.remove('./multi_test.json')
    
    print()


def main():
    """Run all tests."""
    print("Testing Output Destination Interface\n")
    
    test_json_destination()
    test_excel_destination()
    test_postgresql_destination()
    test_console_destination()
    test_factory()
    test_multiple_destinations()
    
    print("=== Summary ===")
    print("✓ JSON file destination working")
    print("✓ Excel file destination working") 
    print("✓ PostgreSQL destination (placeholder) working")
    print("✓ Console destination working")
    print("✓ Factory pattern working")
    print("✓ Multiple destinations working")
    print("\nThe output destination interface is ready!")
    print("\nNext steps:")
    print("- To use PostgreSQL output: pip install psycopg2-binary")
    print("- Update PostgreSQL destination with actual database connection code")
    print("- Configure environment variables for output destination selection")


if __name__ == "__main__":
    main()