#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 12:47:24 2026

@author: kalebpagel
"""

import yfinance as yf

print("\n===== AUTO DCF VALUATION =====\n")

# Get ticker
ticker = input("Enter stock ticker: ").upper()

try:
    stock = yf.Ticker(ticker)
    info = stock.info
except:
    print("Error fetching data.")
    quit()

# Auto data
price = info.get("currentPrice", 0)
revenue = info.get("totalRevenue", 0)
shares = info.get("sharesOutstanding", 1)
debt = info.get("totalDebt", 0)
cash = info.get("totalCash", 0)

print("\n--- AUTO-FILLED DATA ---")
print("Price:", price)
print("Revenue:", revenue)
print("Shares:", shares)
print("Debt:", debt)
print("Cash:", cash)

# Safe input function
def get_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except:
            print("Enter a valid number.")

growth = get_float("Growth Rate (e.g. 0.05): ")
ebit_margin = get_float("EBIT Margin (e.g. 0.20): ")
tax_rate = get_float("Tax Rate (e.g. 0.25): ")
reinvest = get_float("Reinvestment Rate (e.g. 0.30): ")
wacc = get_float("WACC (e.g. 0.10): ")
terminal = get_float("Terminal Growth (e.g. 0.03): ")
years = int(get_float("Projection Years: "))

# Check inputs
if wacc <= terminal:
    print("\nERROR: WACC must be greater than terminal growth.")
    quit()

# DCF
rev = revenue
fcf_total = 0

print("\n--- PROJECTIONS ---")

for i in range(1, years + 1):
    rev = rev * (1 + growth)
    ebit = rev * ebit_margin
    nopat = ebit * (1 - tax_rate)
    fcf = nopat * (1 - reinvest)

    discounted = fcf / ((1 + wacc) ** i)
    fcf_total += discounted

    print("Year", i)
    print(" Revenue:", round(rev, 2))
    print(" FCF:", round(fcf, 2))
    print(" Discounted:", round(discounted, 2))
    print("------------------")

# Terminal value
terminal_fcf = fcf * (1 + terminal)
terminal_value = terminal_fcf / (wacc - terminal)
terminal_discounted = terminal_value / ((1 + wacc) ** years)

# Final values
enterprise = fcf_total + terminal_discounted
equity = enterprise - debt + cash
intrinsic = equity / shares

print("\n===== RESULTS =====")
print("Intrinsic Value:", round(intrinsic, 2))
print("Market Price:", price)

if intrinsic > price:
    print("UNDERVALUED by", round(intrinsic - price, 2))
else:
    print("OVERVALUED by", round(price - intrinsic, 2))