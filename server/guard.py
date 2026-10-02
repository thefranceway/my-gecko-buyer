"""Project 03 guard: is_public_url.

Decision: if a hostname does not resolve, we return False (fail-closed).
Reason: an unresolvable internal name could be an SSRF attempt via DNS
that only resolves inside the target network, or a typo that would bypass
a check. Failing closed avoids letting a private host through because we
could not see its private IP.
Standard library only.
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

def _is_private_ip(ip: ipaddress._BaseAddress) -> bool:
    # loopback, private, link-local, multicast, reserved, unspecified all count as private
    return (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
        # 0.0.0.0/8 and similar are caught by unspecified/reserved, but be explicit
    )

def is_public_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    # must be https only
    if parsed.scheme.lower()!= "https":
        return False

    host = parsed.hostname
    if not host:
        return False

    # try literal IP first
    try:
        ip = ipaddress.ip_address(host)
        return not _is_private_ip(ip)
    except ValueError:
        pass

    # not a literal IP: resolve DNS, every resolved IP must be public
    try:
        # getaddrinfo returns (family, type, proto, canonname, sockaddr)
        # sockaddr[0] is IP string
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError, ValueError):
        # fail-closed: if we cannot resolve, treat as private / not public
        return False

    if not infos:
        return False

    found_public = False
    for family, _, _, _, sockaddr in infos:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if _is_private_ip(ip):
            return False
        found_public = True

    return found_public
