import os
from phkit.chinese.number import say_number

from typing import Optional, List, Dict, Any

SLOT_STATE = 'state'
SLOT_METADATA = 'metadata'

API_SERVER_URL = os.environ.get('API_SERVER_URL', 'http://localhost:8002')
if API_SERVER_URL is None:
    API_SERVER_URL = 'http://localhost:8002'

def url(path: str) -> str:
    return f"{API_SERVER_URL}{path}"

def get_natural_number(number: str) -> int:
    """if number is not natural number, return -1"""
    try:
        result = int(number)
        return -1 if result < 0 else result
    except ValueError:
        return -1

def convert_number_to_chinese(number: int) -> Optional[str]:
    if number < 0:
        return None
    x = str(number)
    if x == '2':
        return '两'
    else:
        return say_number(x)

def convert_metadata_to_content(metadata: Dict[str, Any]) -> str:
    if 'items' not in metadata or not isinstance(metadata['items'], list) or len(metadata['items']) == 0:
        raise ValueError('no items')

    items = metadata['items']

    result = []
    for item in items:
        if 'name' in item and 'quantity' in item:
            quantity_str = convert_number_to_chinese(get_natural_number(item['quantity']))
            result.append(f"{quantity_str}份{item['name']}")

    return concatenate_items_naturally(result)

def concatenate_items_naturally(items: List[str]) -> str:
    result = ''
    for i, item in enumerate(items):
        result += item
        if i < len(items) - 2:
            result += '，'
        elif i < len(items) - 1:
            result += '，还有'

    return result
