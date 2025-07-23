import ipaddress
import socket
from urllib.request import urlopen


def get_public_ip():
    try:
        ipv4 = urlopen("http://ipv4.icanhazip.com").read().decode().strip()
    except Exception:
        ipv4 = None
    try:
        ipv6 = urlopen("http://ipv6.icanhazip.com").read().decode().strip()
    except Exception:
        ipv6 = None

    return ipv4, ipv6


def get_ip(local=False):
    # FIX: Does not work with Tailscale IPs, 100.97.164.37
    addresses = set()
    for entry in socket.getaddrinfo(socket.gethostname(), None):
        # Remove scope ID if present
        iface = ipaddress.ip_interface(str(entry[4][0]).split("%")[0])
        if iface.ip.is_global:
            addresses.add(f"{iface.ip.compressed}")
        if local and (iface.ip.is_link_local or iface.ip.is_private):
            addresses.add(f"{iface.ip.compressed}")
    return addresses
