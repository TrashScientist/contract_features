from datetime import datetime

def parse_date(date_str: str) -> datetime:
    """
    Parse date string in DD.MM.YYYY format to datetime object.
    Returns None if the date string is empty or invalid.
    All datetime objects returned will be timezone-naive.
    """
    if not date_str or date_str == "":
        return None
    
    try:
        parts = date_str.split('.')
        if len(parts) == 3:
            # Ensure we're creating naive datetime objects (no timezone info)
            return datetime.strptime(f"{parts[2]}-{parts[1]}-{parts[0]}", "%Y-%m-%d")
    except Exception:
        # Return None for any parsing errors
        return None
    
    return None