# uInvestor 📈  
*A full-stack stock trading simulation platform*

![Python](https://img.shields.io/badge/Python-3.10-blue)
![Flask](https://img.shields.io/badge/Flask-2.1-black)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey)
![Deployed](https://img.shields.io/badge/Deployed-Render-purple)

🔗 **Live Demo:** https://uinvestor.onrender.com/

▶️ **Youtube Demo** https://youtu.be/LwkaI1PzKoM

📂 **Tech Stack:** Flask · Python · SQLite · Finnhub API · HTML/CSS · Bootstrap

---

## 🚀 Overview

**uInvestor** is a full-stack web application that simulates a real-world stock trading platform.  
Users can register, receive virtual cash, buy and sell real stocks using live market data, track portfolio performance, view transaction history, and compete on a leaderboard.

This project demonstrates **backend engineering**, **API integration**, **database design**, and **production deployment**.

---

## ✨ Features

- Secure user authentication (register/login)
- Real-time stock prices via Finnhub API
- Buy & sell stocks with balance validation
- Portfolio tracking with profit/loss calculation
- Transaction history with timestamps
- Skill-based leaderboard with ranking display
- Gold / Silver / Bronze placement styling
- Deployed to production using Render

---

## 🛠️ Setup Instructions (Local)

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/uInvestor.git
cd uInvestor
```
### 2. Create the virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
FINNHUB_API_KEY=your_finnhub_api_key_here
FLASK_ENV=development
```

### 5.Initialize database
```bash
sqlite3 finance.db < schema.sql
```

### 6. Run the app
```bash
flask run
```
