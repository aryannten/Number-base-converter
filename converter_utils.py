import logging
from typing import Tuple, Dict, List, Union
from decimal import Decimal, getcontext
import json
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure decimal precision
getcontext().prec = 20

def get_base_value(base_name: str) -> int:
    """Get the numerical base value from the base name.
    
    Args:
        base_name: Name of the base (e.g., "Decimal", "Binary")
    
    Returns:
        The integer value of the base (e.g., 10 for Decimal)
    """
    base_map: Dict[str, int] = {
        "Decimal": 10,
        "Binary": 2,
        "Octal": 8,
        "Hexadecimal": 16
    }
    return base_map.get(base_name, 10)

def validate_number(number_str: str, base_name: str) -> Tuple[bool, str]:
    """Validate if a number string is valid for the given base.
    
    Args:
        number_str: The number string to validate
        base_name: Name of the base to validate against
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if '.' in number_str:
            # Validate floating point number
            integer_part, fractional_part = number_str.split('.')
            int(integer_part, get_base_value(base_name))
            # Validate fractional part
            for char in fractional_part:
                if not char.isdigit() and char.upper() not in 'ABCDEF'[:get_base_value(base_name)-10]:
                    raise ValueError
        else:
            int(number_str, get_base_value(base_name))
        return True, ""
    except ValueError:
        return False, f"Invalid {base_name.lower()} number"

def convert_number_logic(number_str: str, from_base: str, to_base: str) -> str:
    """Convert a number from one base to another with floating point support.
    
    Args:
        number_str: The number string to convert
        from_base: Source base name
        to_base: Target base name
    
    Returns:
        The converted number as a string
    
    Raises:
        ValueError: If conversion fails
    """
    try:
        from_base_value = get_base_value(from_base)
        to_base_value = get_base_value(to_base)
        
        if '.' in number_str:
            # Handle floating point conversion
            integer_part, fractional_part = number_str.split('.')
            decimal_value = Decimal(int(integer_part, from_base_value))

            # Convert fractional part
            for i, digit in enumerate(fractional_part, 1):
                if digit.isdigit():
                    digit_value = int(digit)
                else:
                    digit_value = int(digit, 16)  # For hex digits
                decimal_value += Decimal(digit_value) / (Decimal(from_base_value) ** i)

            if to_base == "Decimal":
                return str(decimal_value)
            else:
                # Convert decimal to target base (integer part)
                integer_result = ""
                temp = int(decimal_value)
                if temp == 0:
                    integer_result = "0"
                else:
                    while temp > 0:
                        remainder = temp % to_base_value
                        if remainder < 10:
                            integer_result = str(remainder) + integer_result
                        else:
                            integer_result = chr(55 + remainder) + integer_result
                        temp = temp // to_base_value

                # Convert fractional part
                fractional_result = ""
                fractional = decimal_value - int(decimal_value)
                if fractional > 0:
                    fractional_result = "."
                    for _ in range(10):  # Limit precision to 10 fractional digits
                        fractional *= to_base_value
                        digit = int(fractional)
                        if digit < 10:
                            fractional_result += str(digit)
                        else:
                            fractional_result += chr(55 + digit)
                        fractional -= digit
                        if fractional == 0:
                            break

                return integer_result + fractional_result
        else:
            # Integer conversion
            decimal_value = int(number_str, from_base_value)
            
            if to_base == "Decimal":
                return str(decimal_value)
            elif to_base == "Binary":
                return bin(decimal_value)[2:]
            elif to_base == "Octal":
                return oct(decimal_value)[2:]
            elif to_base == "Hexadecimal":
                return hex(decimal_value)[2:].upper()
            else:
                return str(decimal_value)
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        raise ValueError(f"Failed to convert {number_str} from {from_base} to {to_base}") from e

def get_prefixed_result(result: str, base: str) -> str:
    """Add the appropriate prefix to the result based on the base.
    
    Args:
        result: The converted number string
        base: The target base name
    
    Returns:
        The prefixed result string
    """
    prefixes: Dict[str, str] = {
        "Binary": "0b",
        "Octal": "0o",
        "Hexadecimal": "0x",
        "Decimal": ""
    }
    return f"{prefixes.get(base, '')}{result}"

def save_to_history(history_file: Union[str, Path], input_val: str, from_base: str, result: str, to_base: str) -> None:
    """Save a conversion to the history file.
    
    Args:
        history_file: Path to the history file
        input_val: Input value that was converted
        from_base: Source base
        result: Conversion result
        to_base: Target base
    """
    try:
        history_file = Path(history_file)
        line = f"{input_val} ({from_base}) -> {result} ({to_base})\n"
        with history_file.open('a', encoding='utf-8') as f:
            f.write(line)
    except IOError as e:
        logger.error(f"Failed to save to history: {e}")

def read_history(history_file: Union[str, Path]) -> List[str]:
    """Read the last 5 entries from the history file.
    
    Args:
        history_file: Path to the history file
    
    Returns:
        List of history entries (empty list if file doesn't exist)
    """
    try:
        history_file = Path(history_file)
        with history_file.open('r', encoding='utf-8') as f:
            return f.readlines()[-5:]
    except FileNotFoundError:
        return []
    except IOError as e:
        logger.error(f"Failed to read history: {e}")
        return []