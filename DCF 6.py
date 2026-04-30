#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 30 13:33:01 2026

@author: kalebpagel
"""

import streamlit as st

st.title("DCF Valuation App")

# -------------------------------
# USER INPUTS (NO input())
# -------------------------------
ticker = st.text_input("Stock Name or Ticker")

revenue = st.number_input("Revenue", value=1000000.0)
price = st.number_input("Stock Price", value=100.0)
shares = st.number_input("Shares Outstanding", value=1000000.0)
debt = st.number_input("Debt", value=0.0)
cash = st.number_input("Cash", value=0.0)

st.subheader("Assumptions")

growth = st.number_input("Growth Rate (0.05)", value=0.05)
margin = st.number_input("EBIT Margin (0.20)", value=0.20)
tax = st.number_input("Tax Rate (0.25)", value=0.25)
reinvest = st.number_input("Reinvestment Rate (0.30)", value=0.30)
wacc = st.number_input("WACC (0.10)", value=0.10)
terminal = st.number_input("Terminal Growth (0.03)", value=0.03)
years = int(st.number_input("Years", value=5))

# -------------------------------
# BUTTON TO RUN MODEL
# -------------------------------
if st.button("Run DCF"):

    if wacc <= terminal:
        st.error("WACC must be greater than terminal growth")
    else:
        rev = revenue
        total = 0

        st.subheader("Projections")

        for i in range(1, years + 1):
            rev *= (1 + growth)
            fcf = rev * margin * (1 - tax) * (1 - reinvest)
            disc = fcf / ((1 + wacc) ** i)
            total += disc

            st.write(f"Year {i}: Revenue={round(rev,2)}, FCF={round(fcf,2)}, Discounted={round(disc,2)}")

        terminal_fcf = fcf * (1 + terminal)
        terminal_val = terminal_fcf / (wacc - terminal)
        terminal_disc = terminal_val / ((1 + wacc) ** years)

        enterprise = total + terminal_disc
        equity = enterprise - debt + cash
        intrinsic = equity / shares

        st.subheader("Results")
        st.write("Intrinsic Value:", round(intrinsic, 2))
        st.write("Market Price:", price)

        if intrinsic > price:
            st.success(f"UNDERVALUED by {round(intrinsic - price, 2)}")
        else:
            st.error(f"OVERVALUED by {round(price - intrinsic, 2)}")