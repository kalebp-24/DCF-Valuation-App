#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 12:50:53 2026

@author: kalebpagel
"""

print("\n===== DCF VALUATION APP =====\n")

# -------------------------------
# TRY TO IMPORT YFINANCE
# -------------------------------
use_auto = True

try:
    import yfinance as yf
except:
    print("yfinance not installed → switching to manual mode\n")
    use_auto = False

# -------------------------------
# GET BASIC DATA
# -------------------------------
if use_auto:
    ticker = input("Enter stock ticker: ").upper()

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        price = info.get("currentPrice", 0)
        revenue = info.get("totalRevenue", 0)
        shares = info.get("sharesOutstanding", 1)
        debt = info.get("totalDebt", 0)
        cash = info.get("totalCash", 0)

        print("\n--- AUTO DATA ---")
        print("Price:", price)
        print("Revenue:", revenue)
        print("Shares:", shares)
        print("Debt:", debt)
        print("Cash:", cash)

        # If data is missing → fallback
        if revenue == 0 or shares == 0:
            print("\nMissing data → switching to manual mode\n")
            use_auto = False

    except:
        print("Error fetching data → switching to manual mode\n")
        use_auto = False

# -------------------------------
# MANUAL INPUT (ALWAYS SAFE)
# -------------------------------
if not use_auto:
    ticker = input("Stock Name: ")
    revenue = float(input("Revenue: "))
    price = float(input("Stock Price: "))
    shares = float(input("Shares: "))
    debt = float(input("Debt: "))
    cash = float(input("Cash: "))

# -------------------------------
# SAFE INPUT FUNCTION
# -------------------------------
def get_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except:
            print("Enter a valid number.")

# -------------------------------
# ASSUMPTIONS
# -------------------------------
growth = get_float("Growth Rate (0.05): ")
margin = get_float("EBIT Margin (0.20): ")
tax = get_float("Tax Rate (0.25): ")
reinvest = get_float("Reinvestment Rate (0.30): ")
wacc = get_float("WACC (0.10): ")
terminal = get_float("Terminal Growth (0.03): ")
years = int(get_float("Years: "))

# -------------------------------
# VALIDATION
# -------------------------------
if wacc <= terminal:
    print("\nERROR: WACC must be greater than terminal growth.")
    quit()

# -------------------------------
# DCF CALCULATION
# -------------------------------
rev = revenue
fcf_total = 0

print("\n--- PROJECTIONS ---")

for i in range(1, years + 1):
    rev = rev * (1 + growth)
    ebit = rev * margin
    nopat = ebit * (1 - tax)
    fcf = nopat * (1 - reinvest)

    discounted = fcf / ((1 + wacc) ** i)
    fcf_total += discounted

    print("Year", i)
    print(" Revenue:", round(rev, 2))
    print(" FCF:", round(fcf, 2))
    print(" Discounted:", round(discounted, 2))
    print("------------------")

# -------------------------------
# TERMINAL VALUE
# -------------------------------
terminal_fcf = fcf * (1 + terminal)
terminal_value = terminal_fcf / (wacc - terminal)
terminal_discounted = terminal_value / ((1 + wacc) ** years)

# -------------------------------
# FINAL VALUATION
# -------------------------------
enterprise = fcf_total + terminal_discounted
equity = enterprise - debt + cash
intrinsic = equity / shares

# -------------------------------
# RESULTS
# -------------------------------
print("\n===== RESULTS =====")
print("Stock:", ticker)
print("Intrinsic Value:", round(intrinsic, 2))
print("Market Price:", round(price, 2))

if intrinsic > price:
    print("UNDERVALUED by", round(intrinsic - price, 2))
else:
    print("OVERVALUED by", round(price - intrinsic, 2))

print("\n===== DONE =====\n")