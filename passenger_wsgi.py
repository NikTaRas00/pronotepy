import traceback

try:
    from app import app as application  # entry point for cPanel "Setup Python App" (Passenger)
except Exception:
    # TEMPORARY DEBUG: show the startup error in the browser instead of Passenger's generic page.
    # Remove this try/except once the app starts, so tracebacks aren't public.
    _error = traceback.format_exc()

    def application(environ, start_response):
        start_response("500 Internal Server Error", [("Content-Type", "text/plain; charset=utf-8")])
        return [_error.encode("utf-8")]
