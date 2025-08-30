
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters

cookie_params = CookieParameters()

cookie = SessionCookie(
    cookie_name="session",
    identifier="general_verifier",
    auto_error=False,
    secret_key="your-secret-key-change-this",  # cambia con una chiave sicura!
    cookie_params=cookie_params,
)