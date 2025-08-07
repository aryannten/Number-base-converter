import unittest
from converter_utils import (
    get_base_value,
    validate_number,
    convert_number_logic,
    get_prefixed_result,
    save_to_history,
    read_history
)
from pathlib import Path
import tempfile
import os

class TestConverterUtils(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for history file tests
        self.test_dir = tempfile.TemporaryDirectory()
        self.history_file = Path(self.test_dir.name) / "test_history.txt"
    
    def tearDown(self):
        # Clean up the temporary directory
        self.test_dir.cleanup()
    
    def test_get_base_value(self):
        self.assertEqual(get_base_value("Decimal"), 10)
        self.assertEqual(get_base_value("Binary"), 2)
        self.assertEqual(get_base_value("Octal"), 8)
        self.assertEqual(get_base_value("Hexadecimal"), 16)
        self.assertEqual(get_base_value("Unknown"), 10)  # Default
    
    def test_validate_number(self):
        # Valid numbers
        self.assertEqual(validate_number("1010", "Binary"), (True, ""))
        self.assertEqual(validate_number("755", "Octal"), (True, ""))
        self.assertEqual(validate_number("123", "Decimal"), (True, ""))
        self.assertEqual(validate_number("FF", "Hexadecimal"), (True, ""))
        
        # Invalid numbers
        self.assertEqual(validate_number("102", "Binary"), (False, "Invalid binary number"))
        self.assertEqual(validate_number("89", "Octal"), (False, "Invalid octal number"))
        self.assertEqual(validate_number("GH", "Hexadecimal"), (False, "Invalid hexadecimal number"))
        
        # Floating point numbers
        self.assertEqual(validate_number("1010.101", "Binary"), (True, ""))
        self.assertEqual(validate_number("755.7", "Octal"), (True, ""))
        self.assertEqual(validate_number("123.456", "Decimal"), (True, ""))
        self.assertEqual(validate_number("FF.A", "Hexadecimal"), (True, ""))
        
        # Invalid floating point
        self.assertEqual(validate_number("102.3", "Binary"), (False, "Invalid binary number"))
        self.assertEqual(validate_number("89.9", "Octal"), (False, "Invalid octal number"))
    
    def test_convert_number_logic_integer(self):
        # Binary conversions
        self.assertEqual(convert_number_logic("1010", "Binary", "Decimal"), "10")
        self.assertEqual(convert_number_logic("1010", "Binary", "Octal"), "12")
        self.assertEqual(convert_number_logic("1010", "Binary", "Hexadecimal"), "A")
        
        # Decimal conversions
        self.assertEqual(convert_number_logic("10", "Decimal", "Binary"), "1010")
        self.assertEqual(convert_number_logic("10", "Decimal", "Octal"), "12")
        self.assertEqual(convert_number_logic("10", "Decimal", "Hexadecimal"), "A")
        
        # Octal conversions
        self.assertEqual(convert_number_logic("12", "Octal", "Decimal"), "10")
        self.assertEqual(convert_number_logic("12", "Octal", "Binary"), "1010")
        self.assertEqual(convert_number_logic("12", "Octal", "Hexadecimal"), "A")
        
        # Hexadecimal conversions
        self.assertEqual(convert_number_logic("A", "Hexadecimal", "Decimal"), "10")
        self.assertEqual(convert_number_logic("A", "Hexadecimal", "Binary"), "1010")
        self.assertEqual(convert_number_logic("A", "Hexadecimal", "Octal"), "12")
    
    def test_convert_number_logic_floating(self):
        # Binary floating point
        self.assertEqual(convert_number_logic("1010.101", "Binary", "Decimal"), "10.625")
        self.assertEqual(convert_number_logic("1010.101", "Binary", "Octal"), "12.5")
        self.assertEqual(convert_number_logic("1010.101", "Binary", "Hexadecimal"), "A.A")
        
        # Decimal floating point
        self.assertEqual(convert_number_logic("10.625", "Decimal", "Binary"), "1010.101")
        self.assertEqual(convert_number_logic("10.625", "Decimal", "Octal"), "12.5")
        self.assertEqual(convert_number_logic("10.625", "Decimal", "Hexadecimal"), "A.A")
        
        # Limited precision checks
        result = convert_number_logic("0.1", "Decimal", "Binary")
        self.assertTrue(result.startswith("0.0001100110011"))
    
    def test_get_prefixed_result(self):
        self.assertEqual(get_prefixed_result("1010", "Binary"), "0b1010")
        self.assertEqual(get_prefixed_result("12", "Octal"), "0o12")
        self.assertEqual(get_prefixed_result("A", "Hexadecimal"), "0xA")
        self.assertEqual(get_prefixed_result("10", "Decimal"), "10")
    
    def test_history_functions(self):
        # Test save and read
        save_to_history(self.history_file, "1010", "Binary", "10", "Decimal")
        save_to_history(self.history_file, "A", "Hexadecimal", "10", "Decimal")
        
        history = read_history(self.history_file)
        self.assertEqual(len(history), 2)
        self.assertIn("1010 (Binary) -> 10 (Decimal)", history[0])
        self.assertIn("A (Hexadecimal) -> 10 (Decimal)", history[1])
        
        # Test with more than 5 entries
        for i in range(10):
            save_to_history(self.history_file, str(i), "Decimal", str(i), "Binary")
        
        history = read_history(self.history_file)
        self.assertEqual(len(history), 5)  # Should only return last 5
    
    def test_nonexistent_history_file(self):
        # Test with non-existent file
        nonexistent_file = Path(self.test_dir.name) / "nonexistent.txt"
        history = read_history(nonexistent_file)
        self.assertEqual(history, [])


if __name__ == '__main__':
    unittest.main()