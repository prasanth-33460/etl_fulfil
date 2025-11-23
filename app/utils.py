import socket
import ipaddress
from urllib.parse import urlparse

def validate_webhook_url(url: str) -> str:
    """
    Validates a webhook URL to prevent SSRF attacks.
    Ensures the URL scheme is http/https and the host is not a private/loopback IP.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        raise ValueError("Invalid URL format")

    if parsed.scheme not in ('http', 'https'):
        raise ValueError("Only HTTP and HTTPS schemes are allowed")

    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid hostname")

    try:
        # Resolve hostname to IP
        ip = socket.gethostbyname(hostname)
        ip_addr = ipaddress.ip_address(ip)
        
        # Check for private or loopback addresses
        if ip_addr.is_private or ip_addr.is_loopback:
            raise ValueError(f"URL resolves to a restricted IP address: {ip}")
            
    except socket.gaierror:
        raise ValueError("Could not resolve hostname")
    except ValueError as e:
        raise e
    except Exception as e:
        raise ValueError(f"URL validation failed: {str(e)}")

    return url
