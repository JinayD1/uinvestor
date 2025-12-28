#!/usr/bin/python
import os
from datetime import datetime
from json import load
from dotenv import load_dotenv
import sqlite3
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# ---------------- CONFIG ----------------
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

app.jinja_env.filters["usd"] = usd

app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

DATABASE = "finance.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def execute(query, **params):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, params)
    if query.strip().upper().startswith("SELECT"):
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    conn.commit()
    conn.close()

if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

# ---------------- INDEX ----------------
@app.route("/")
@login_required
def index():
    stocks_owned = execute(
        "SELECT * FROM portfolio WHERE id=:id GROUP BY stock",
        id=session["user_id"]
    )

    stocks = []
    for stock in stocks_owned:
        q = lookup(stock["stock"])
        if not q:
            continue
        stocks.append({
            "symbol": stock["stock"],
            "price": usd(stock["price"]),
            "volume": stock["volume"],
            "value": usd(stock["price"] * stock["volume"]),
            "profit": usd(stock["volume"] * q["price"] - stock["volume"] * stock["price"]),
            "current": usd(q["price"])
        })

    cash = execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])
    return render_template("index.html", stocks=stocks, cash=usd(cash[0]["cash"]))

# ---------------- BUY ----------------
@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "GET":
        return render_template("buy.html")

    symbol = request.form.get("stock_symbol", "").strip().upper()
    qty = request.form.get("quantity")

    if not symbol:
        return apology("must provide stock symbol")
    if not qty or int(qty) <= 0:
        return apology("quantity invalid")

    quote = lookup(symbol)
    if not quote:
        return apology("invalid stock symbol")

    cost = quote["price"] * int(qty)
    cash = execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])[0]["cash"]

    if cash < cost:
        return apology("not enough cash")

    execute("UPDATE users SET cash=:c WHERE id=:id", c=cash - cost, id=session["user_id"])

    owned = execute(
        "SELECT * FROM portfolio WHERE id=:id AND stock=:s",
        id=session["user_id"], s=symbol
    )

    if not owned:
        execute(
            "INSERT INTO portfolio (id, stock, volume, price) VALUES (:id,:s,:v,:p)",
            id=session["user_id"], s=symbol, v=int(qty), p=quote["price"]
        )
    else:
        execute(
            "UPDATE portfolio SET volume=:v WHERE id=:id AND stock=:s",
            v=owned[0]["volume"] + int(qty), id=session["user_id"], s=symbol
        )

    execute(
        "INSERT INTO transactions (id, stock, volume, price, date, method) VALUES (:id,:s,:v,:p,:d,'BUY')",
        id=session["user_id"], s=symbol, v=int(qty), p=usd(quote["price"]),
        d=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    return redirect("/")

# ---------------- SELL ----------------
@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    if request.method == "GET":
        return render_template("sell.html")

    symbol = request.form.get("stock_symbol", "").strip().upper()
    qty = request.form.get("quantity")

    if not symbol:
        return apology("must provide stock symbol")
    if not qty or int(qty) <= 0:
        return apology("quantity invalid")

    quote = lookup(symbol)
    if not quote:
        return apology("invalid stock symbol")

    owned = execute(
        "SELECT volume, price FROM portfolio WHERE id=:id AND stock=:s",
        id=session["user_id"], s=symbol
    )

    if not owned or int(qty) > owned[0]["volume"]:
        return apology("not enough shares")

    value = quote["price"] * int(qty)
    cash = execute("SELECT cash FROM users WHERE id=:id", id=session["user_id"])[0]["cash"]

    execute("UPDATE users SET cash=:c WHERE id=:id", c=cash + value, id=session["user_id"])

    remaining = owned[0]["volume"] - int(qty)
    if remaining == 0:
        execute("DELETE FROM portfolio WHERE id=:id AND stock=:s", id=session["user_id"], s=symbol)
    else:
        execute(
            "UPDATE portfolio SET volume=:v WHERE id=:id AND stock=:s",
            v=remaining, id=session["user_id"], s=symbol
        )

    execute(
        "INSERT INTO transactions (id, stock, volume, price, date, method) VALUES (:id,:s,:v,:p,:d,'SELL')",
        id=session["user_id"], s=symbol, v=int(qty), p=quote["price"],
        d=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    return redirect("/")

# ---------------- QUOTE ----------------
@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == "GET":
        return render_template("quote.html")

    symbol = request.form.get("stock_symbol", "").strip().upper()
    if not symbol:
        return apology("must provide stock symbol")

    q = lookup(symbol)
    if not q:
        return apology("invalid stock symbol")

    return render_template("quoted.html", name=q["name"], symbol=q["symbol"], price=usd(q["price"]))

# ---------------- xTORY (RESTORED) ----------------
@app.route("/history")
@login_required
def history():
    transactions = execute(
        "SELECT * FROM transactions WHERE id=:id ORDER BY date DESC",
        id=session["user_id"]
    )

    if not transactions:
        return apology("No transactions made")

    return render_template("history.html", stocks=transactions)

# ---------------- LEADERBOARD ----------------
@app.route("/leaderboard")
@login_required
def leaderboard():
    leaderboard = []

    skill = execute(
        "SELECT experience FROM users WHERE id = :id",
        id=session["user_id"]
    )[0]["experience"]

    profits = execute("""
        SELECT
            users.id,
            users.username,
            COALESCE(leaderboard.profit, 0) AS profit
        FROM users
        LEFT JOIN leaderboard ON users.id = leaderboard.id
        WHERE users.experience = :e
        ORDER BY profit DESC
    """, e=skill)

    user_entry = None

    for i, p in enumerate(profits):
        entry = {
            "placement": i + 1,
            "username": p["username"],
            "profit": usd(p["profit"])
        }

        leaderboard.append(entry)

        if p["id"] == session["user_id"]:
            user_entry = entry

    return render_template(
        "leaderboard.html",
        profits=leaderboard,
        user=user_entry,
        skill=skill
    )

# ---------------- AUTH ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        rows = execute("SELECT * FROM users WHERE username=:u", u=request.form.get("username"))
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)
        session["user_id"] = rows[0]["id"]
        return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        execute(
            "INSERT INTO users (username, hash, experience) VALUES (:u,:h,:e)",
            u=request.form.get("username"),
            h=generate_password_hash(request.form.get("password")),
            e=request.form.get("experience")
        )
        return redirect("/login")
    return render_template("register.html")

@app.route("/help")
@login_required
def help():
    """
    Display help page explaining how the app works
    """
    return render_template("helper.html")

# ---------------- ERRORS ----------------
def errorhandler(e):
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

for code in default_exceptions:
    app.errorhandler(code)(errorhandler)