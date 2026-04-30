#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 12:34:11 2026

@author: kalebpagel
"""

print("\n===== DCF VALUATION MODEL (SAFE VERSION) =====\n")

# -------------------------------
# SAFE INPUT FUNCTION
# -------------------------------
def get_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except:
            print("Invalid input. Please enter a number.")

def get_int(prompt):
    while True:
        try:
            return int(input(prompt))
        except:
            print("Invalid input. Please enter a whole number.")

# -------------------------------
# INPUTS
# -------------------------------
revenue = get_float("Current Revenue: ")
price = get_float("Current Stock Price: ")
shares = get_float("Shares Outstanding: ")
debt = get_float("Total Debt: ")
cash = get_float("Cash: ")

growth = get_float("Revenue Growth Rate (e.g. 0.05): ")
ebit_margin = get_float("EBIT Margin (e.g. 0.20): ")
tax_rate = get_float("Tax Rate (e.g. 0.25): ")
reinvest_rate = get_float("Reinvestment Rate (e.g. 0.30): ")
wacc = get_float("WACC (e.g. 0.10): ")
terminal_growth = get_float("Terminal Growth Rate (e.g. 0.03): ")
years = get_int("Projection Years: ")

# -------------------------------
# VALIDATION
# -------------------------------
if wacc <= terminal_growth:
    print("\nERROR: WACC must be greater than terminal growth rate.")
    print("Fix your inputs and run again.\n")
else:

    # -------------------------------
    # DCF CALCULATION
    # -------------------------------
    rev = revenue
    fcf_list = []
    discounted_list = []

    print("\n----- YEARLY PROJECTIONS -----\n")

    for year in range(1, years + 1):
        rev = rev * (1 + growth)
        ebit = rev * ebit_margin
        nopat = ebit * (1 - tax_rate)
        fcf = nopat * (1 - reinvest_rate)

        discount_factor = (1 + wacc) ** year
        discounted_fcf = fcf / discount_factor

        fcf_list.append(fcf)
        discounted_list.append(discounted_fcf)

        print("Year", year)
        print(" Revenue:", round(rev, 2))
        print(" FCF:", round(fcf, 2))
        print(" Discounted FCF:", round(discounted_fcf, 2))
        print("---------------------")

    # -------------------------------
    # TERMINAL VALUE
    # -------------------------------
    terminal_fcf = fcf_list[-1] * (1 + terminal_growth)
    terminal_value = terminal_fcf / (wacc - terminal_growth)
    terminal_discounted = terminal_value / ((1 + wacc) ** years)

    # -------------------------------
    # FINAL VALUES
    # -------------------------------
    enterprise_value = sum(discounted_list) + terminal_discounted
    equity_value = enterprise_value - debt + cash
    intrinsic_value = equity_value / shares

    # -------------------------------
    # OUTPUT
    # -------------------------------
    print("\n==============================")
    print("        FINAL RESULTS")
    print("==============================\n")

    print("Enterprise Value:", round(enterprise_value, 2))
    print("Equity Value:", round(equity_value, 2))
    print("Intrinsic Value per Share:", round(intrinsic_value, 2))
    print("Market Price:", round(price, 2))

    print("\n------------------------------")

    if intrinsic_value > price:
        print("UNDERVALUED by:", round(intrinsic_value - price, 2))
    else:
        print("OVERVALUED by:", round(price - intrinsic_value, 2))

    print("\n===== MODEL COMPLETE =====\n")