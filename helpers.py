import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol using Finnhub."""
    try:
        api_key = os.environ.get("API_KEY")
        if not api_key:
            return None

        url = "https://finnhub.io/api/v1/quote"
        params = {
            "symbol": symbol.upper(),
            "token": api_key
        }

        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        # Finnhub returns 0 if symbol is invalid
        if data.get("c") is None or data.get("c") == 0:
            return None

        return {
            "name": symbol.upper(),   # Finnhub quote endpoint doesn't include name
            "price": float(data["c"]),
            "symbol": symbol.upper()
        }

    except (requests.RequestException, KeyError, ValueError):
        return None

def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
