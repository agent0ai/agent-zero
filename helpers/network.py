import socket
import struct


def is_loopback_address(address: str) -> bool:
    """Check whether *address* resolves to a loopback interface."""
    _checkers = {
        socket.AF_INET: lambda x: (
            struct.unpack("!I", socket.inet_aton(x))[0] >> (32 - 8)
        ) == 127,
        socket.AF_INET6: lambda x: x == "::1",
    }
    try:
        socket.inet_pton(socket.AF_INET6, address)
        return _checkers[socket.AF_INET6](address)
    except socket.error:
        pass
    try:
        socket.inet_pton(socket.AF_INET, address)
        return _checkers[socket.AF_INET](address)
    except socket.error:
        pass
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            r = socket.getaddrinfo(address, None, family, socket.SOCK_STREAM)
        except socket.gaierror:
            return False
        for fam, _, _, _, sockaddr in r:
            if not _checkers[fam](sockaddr[0]):
                return False
    return True
