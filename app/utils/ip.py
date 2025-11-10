"""Utility helpers for working with IP addresses."""

from ipaddress import ip_address, IPv4Address, IPv6Address, ip_network
from typing import Optional, List
from fastapi import Request


def normalize_ip(raw_ip: Optional[str]) -> Optional[str]:
    """Return a normalized string representation of the IP address."""
    if not raw_ip:
        return None
    try:
        addr = ip_address(raw_ip)
    except ValueError:
        return None
    return addr.compressed


def is_private_ip(raw_ip: Optional[str]) -> bool:
    normalized = normalize_ip(raw_ip)
    if normalized is None:
        return False
    addr = ip_address(normalized)
    return addr.is_private


def is_valid_ip(raw_ip: Optional[str]) -> bool:
    return normalize_ip(raw_ip) is not None


def is_ip_in_cidr_list(ip: str, cidr_list: List[str]) -> bool:
    """Check if an IP address is contained within any of the given CIDR ranges."""
    if not ip:
        return False
    try:
        ip_obj = ip_address(ip)
        return any(ip_obj in ip_network(cidr) for cidr in cidr_list)
    except ValueError:
        return False


def get_client_ip(request: Request) -> str:
    """Get the client IP address from a request.
    
    This is a convenience wrapper around extract_client_ip that uses default settings
    for trusted proxies from configuration.
    """
    # Default to common cloud/CDN proxy ranges
    trusted_proxies = [
        "10.0.0.0/8",      # AWS VPC, standard private network
        "172.16.0.0/12",   # Azure, standard private network
        "192.168.0.0/16",  # Standard private network
        "127.0.0.0/8",     # Localhost
        "169.254.0.0/16",  # Link-local
        "fc00::/7",        # Unique local addresses
    ]
    
    # Always honor XFF from trusted proxies
    client_ip = extract_client_ip(request, trusted_proxies, honor_xff=True)
    return client_ip if client_ip else request.client.host


def extract_client_ip(request: Request, trusted_proxies: List[str], honor_xff: bool) -> Optional[str]:
    """Extract the actual client IP address from a request, respecting trusted proxy configuration.
    
    Args:
        request: The FastAPI request object
        trusted_proxies: List of CIDR ranges for trusted proxies
        honor_xff: Whether to honor X-Forwarded-For headers from trusted proxies
        
    Returns:
        Optional[str]: Normalized client IP address, or None if invalid
    """
    # Get the direct peer IP
    if not request.client or not request.client.host:
        return None
    
    peer_ip = request.client.host
    peer_normalized = normalize_ip(peer_ip)
    if peer_normalized is None:
        return None

    # If we don't honor XFF or the peer isn't trusted, use direct peer IP
    if not honor_xff or not is_ip_in_cidr_list(peer_normalized, trusted_proxies):
        return peer_normalized

    # Get leftmost non-proxy IP from XFF
    xff = request.headers.get("x-forwarded-for")
    if not xff:
        return peer_normalized

    # Process the XFF chain from right to left
    ips = [ip.strip() for ip in xff.split(",")]
    ips.append(peer_normalized)  # Add connecting IP to chain
    
    # Return first untrusted IP from the right (closest to our server)
    for ip in reversed(ips):
        normalized = normalize_ip(ip)
        if normalized and not is_ip_in_cidr_list(normalized, trusted_proxies):
            return normalized
            
    # If all IPs are trusted proxies, use the original client
    return normalize_ip(ips[0]) if ips else peer_normalized
