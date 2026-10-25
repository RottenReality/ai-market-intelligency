from fastapi import Request


def client_ip(request: Request, trust_proxy: bool) -> str:
    """Behind the Cloudflare tunnel every request comes from the proxy, so the real
    visitor IP is in CF-Connecting-IP. Only trust that header when configured to."""
    if trust_proxy:
        forwarded = request.headers.get("cf-connecting-ip", "").strip()
        if forwarded:
            return forwarded
    return request.client.host if request.client else "unknown"
