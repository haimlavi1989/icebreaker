"""
Helper functions for the ice breaker generator.
"""
import re
import time
import unicodedata
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

def is_valid_url(url: str) -> bool:
    """Check if a URL is valid.
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def clean_text(text: str) -> str:
    """Clean and normalize text.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Normalize unicode
    text = unicodedata.normalize("NFKD", text)
    
    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    
    return text

def extract_domain(url: str) -> str:
    """Extract the domain from a URL.
    
    Args:
        url: URL to extract domain from
        
    Returns:
        Domain name
    """
    try:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Remove www. prefix if present
        if domain.startswith("www."):
            domain = domain[4:]
        
        return domain
    except:
        return ""

def identify_platform(url: str) -> str:
    """Identify the social media platform from a URL.
    
    Args:
        url: URL to identify platform from
        
    Returns:
        Platform name or "unknown"
    """
    domain = extract_domain(url).lower()
    
    platform_mapping = {
        "linkedin.com": "LinkedIn",
        "twitter.com": "Twitter",
        "x.com": "Twitter",
        "github.com": "GitHub",
        "facebook.com": "Facebook",
        "instagram.com": "Instagram",
        "medium.com": "Medium",
        "scholar.google.com": "Google Scholar",
        "researchgate.net": "ResearchGate",
        "academia.edu": "Academia",
    }
    
    for key, value in platform_mapping.items():
        if key in domain:
            return value
    
    return "unknown"

def rate_limit(max_calls: int, period: float):
    """Decorator to rate limit function calls.
    
    Args:
        max_calls: Maximum number of calls allowed in the period
        period: Time period in seconds
        
    Returns:
        Decorated function
    """
    calls = []
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_time = time.time()
            
            # Remove calls older than the period
            while calls and calls[0] < current_time - period:
                calls.pop(0)
            
            # Check if we've exceeded the rate limit
            if len(calls) >= max_calls:
                # Calculate wait time
                wait_time = calls[0] + period - current_time
                if wait_time > 0:
                    time.sleep(wait_time)
                    # Remove the oldest call that we waited for
                    calls.pop(0)
            
            # Add current call
            calls.append(time.time())
            
            # Execute the function
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

def truncate_text(text: str, max_length: int = 500, add_ellipsis: bool = True) -> str:
    """Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        add_ellipsis: Whether to add ellipsis at the end
        
    Returns:
        Truncated text
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    
    # Try to truncate at a word boundary
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.8:  # Only truncate at word if we're not losing too much
        truncated = truncated[:last_space]
    
    if add_ellipsis:
        truncated += "..."
    
    return truncated

def format_name(name: str) -> str:
    """Format a name properly.
    
    Args:
        name: Name to format
        
    Returns:
        Formatted name
    """
    if not name:
        return ""
    
    # Clean the name
    name = clean_text(name)
    
    # Split by spaces
    parts = name.split()
    
    # Capitalize each part
    formatted_parts = []
    for part in parts:
        # Handle hyphenated names (e.g., "Jean-Paul")
        if "-" in part:
            subparts = part.split("-")
            formatted_parts.append("-".join(sp.capitalize() for sp in subparts))
        else:
            # Handle prefixes like "van", "de", "von", etc.
            prefixes = ["van", "de", "der", "von", "el", "al", "bin", "ibn", "mac", "mc"]
            if part.lower() in prefixes:
                formatted_parts.append(part.lower())
            else:
                formatted_parts.append(part.capitalize())
    
    return " ".join(formatted_parts)

def extract_name_from_email(email: str) -> Optional[str]:
    """Extract a name from an email address.
    
    Args:
        email: Email address
        
    Returns:
        Extracted name or None
    """
    if not email or "@" not in email:
        return None
    
    # Get the local part (before @)
    local_part = email.split("@")[0]
    
    # Replace dots, underscores, hyphens with spaces
    name = re.sub(r"[._-]", " ", local_part)
    
    # Capitalize each word
    name = " ".join(word.capitalize() for word in name.split())
    
    return name if name else None