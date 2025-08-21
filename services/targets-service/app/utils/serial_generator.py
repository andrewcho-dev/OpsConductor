"""
Serial number generator for targets
"""

import random
import string
from datetime import datetime


def generate_target_serial() -> str:
    """
    Generate a unique target serial number
    Format: TGT-YYYYMMDD-XXXX (e.g., TGT-20240101-A1B2)
    """
    # Get current date
    date_str = datetime.utcnow().strftime("%Y%m%d")
    
    # Generate random 4-character suffix (alphanumeric)
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    return f"TGT-{date_str}-{suffix}"


def generate_method_name(method_type: str) -> str:
    """
    Generate a unique method name
    Format: method_type_timestamp (e.g., ssh_1704067200)
    """
    timestamp = int(datetime.utcnow().timestamp())
    return f"{method_type}_{timestamp}"


def generate_credential_name(credential_type: str, username: str) -> str:
    """
    Generate a credential name
    Format: credential_type_username (e.g., password_admin)
    """
    return f"{credential_type}_{username}"