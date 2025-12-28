import os
import requests

from flask import redirect, render_template, request, session
from functools import wraps

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
if not FINNHUB_API_KEY:
    raise RuntimeError("FINNHUB_API_KEY not set")

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        for old, new in [
            ("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
            ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """Decorate routes to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol using Finnhub."""
    if not symbol:
        return None

    try:
        url = "https://finnhub.io/api/v1/quote"
        params = {
            "symbol": symbol.upper(),
            "token": FINNHUB_API_KEY
        }

        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        # Invalid symbol → all values are 0
        if not data or data.get("c", 0) == 0:
            return None

        return {
            "name": symbol.upper(),   # Finnhub quote endpoint has no company name
            "symbol": symbol.upper(),
            "price": float(data["c"])
        }

    except (requests.RequestException, ValueError, KeyError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
