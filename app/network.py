import socket

from app.settings import load_config


def check_internal_network() -> bool:
    cfg = load_config().get("mail", {})
    host = cfg.get("host", "").strip()
    port = int(cfg.get("port", 993))
    if not host:
        return False
    try:
        sock = socket.create_connection((host, port), timeout=3)
        sock.close()
        return True
    except (OSError, socket.gaierror):
        return False
