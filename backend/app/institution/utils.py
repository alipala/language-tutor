"""
Utility functions for institution management
"""
import secrets
import string

def generate_institution_code(institution_name: str) -> str:
    """
    Generate unique institution code
    Format: ACRONYM + 4-digit random number
    Example: Lincoln Academy -> LINCOLN2548
    """
    # Create acronym from institution name
    words = institution_name.upper().split()
    if len(words) > 1:
        acronym = ''.join(word[0] for word in words[:3])  # Max 3 letters
    else:
        acronym = institution_name[:7].upper().replace(' ', '')

    # Add random 4-digit number
    random_digits = ''.join(secrets.choice(string.digits) for _ in range(4))

    return f"{acronym}{random_digits}"
