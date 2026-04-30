#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 29 22:18:12 2026

@author: kalebpagel
"""

print("\n===== DCF VALUATION MODEL =====\n")

# -------------------------------
# INPUTS (ALL MANUAL)
# -------------------------------
revenue = float(input("Current Revenue: "))
price = float(input("Current Stock Price: "))
shares = float(input("Shares Outstanding: "))
debt = float(input("Total Debt: "))
cash = float(input("Cash: "))

growth = float(input("Annual Revenue Growth Rate (e.g. 0.05): "))
ebit_margin = float(input("EBIT Margin (e.g. 0.20): "))
tax_rate = float(input("Tax Rate (e.g. 0.25): "))
reinvest_rate = float(input("Reinvestment Rate (e.g. 0.30): "))
wacc = float(input("WACC (e.g. 0.10): "))
terminal_growth = float(input("Terminal Growth Rate (e.g. 0.03): "))
years = int(input("Projection Years: "))

# -------------------------------
# DCF CALCULATION
# -------------------------------
fcf_list = []
discounted_fcf_list = []

rev = revenue

print("\n----- YEARLY PROJECTIONS -----\n")

for year in range(1, years + 1):
    rev = rev * (1 + growth)
    ebit = rev * ebit_margin
    nopat = ebit * (1 - tax_rate)
    fcf = nopat * (1 - reinvest_rate)

    discount = (1 + wacc) ** year
    discounted_fcf = fcf / discount

    fcf_list.append(fcf)
    discounted_fcf_list.append(discounted_fcf)

    print(f"Year {year}: Revenue={rev:,.2f}, FCF={fcf:,.2f}, Discounted FCF={discounted_fcf:,.2f}")

# -------------------------------
# TERMINAL VALUE
# -------------------------------
terminal_fcf = fcf_list[-1] * (1 + terminal_growth)
terminal_value = terminal_fcf / (wacc - terminal_growth)
terminal_discounted = terminal_value / ((1 + wacc) ** years)

# -------------------------------
# TOTAL VALUE
# -------------------------------
enterprise_value = sum(discounted_fcf_list) + terminal_discounted
equity_value = enterprise_value - debt + cash
intrinsic_value = equity_value / shares

# -------------------------------
# OUTPUT
# -------------------------------
print("\n==============================")
print("        FINAL RESULTS")
print("==============================\n")

print(f"Enterprise Value: ${enterprise_value:,.2f}")
print(f"Equity Value:     ${equity_value:,.2f}")
print(f"Intrinsic Value:  ${intrinsic_value:,.2f}")
print(f"Market Price:     ${price:,.2f}")

print("\n------------------------------")

if intrinsic_value > price:
    print(f"UNDERVALUED by ${intrinsic_value - price:,.2f}")
else:
    print(f"OVERVALUED by ${price - intrinsic_value:,.2f}")

print("\n===== END OF MODEL =====\n")