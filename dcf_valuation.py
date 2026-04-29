# -*- coding: utf-8 -*-
"""
======================================================
  DCF Intrinsic Value Calculator
  A step-by-step Discounted Cash Flow valuation app
  Compatible with Spyder IDE (IPython console)
======================================================

HOW TO RUN IN SPYDER:
  Option 1: Press F5 (Run file) -- the app starts automatically.
  Option 2: In the IPython console, type:  main()

REQUIRED PACKAGES (install once via Anaconda Prompt or terminal):
  pip install yfinance numpy pandas
"""

import yfinance as yf
import numpy as np
import sys
import io
import contextlib

# ─────────────────────────────────────────────────────────────────────────────
#  SPYDER / IPYTHON COMPATIBILITY
#  Force stdout to use UTF-8 so special characters don't crash the console.
# ─────────────────────────────────────────────────────────────────────────────
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass  # older Python versions -- safe to ignore


# =============================================================================
#  DISPLAY HELPERS
# =============================================================================

def header(title):
    print("\n" + "=" * 62)
    print("  " + title)
    print("=" * 62)

def section(title):
    print("\n" + "-" * 62)
    print("  " + title)
    print("-" * 62)

def explain(text):
    """Print an indented explanation block (teaching moment)."""
    for line in text.strip().split("\n"):
        print("    [i] " + line.strip())

def fmt(value, billions=True):
    """Format a dollar value as $XB or $X,XXX."""
    if billions:
        return "${:.2f}B".format(value / 1e9)
    return "${:,.2f}".format(value)

def get_float(prompt, default=None, min_val=None, max_val=None):
    """
    Prompt the user for a numeric input.
    Shows a default value; user presses Enter to accept it.
    Validates the range and re-prompts on bad input.
    """
    while True:
        suffix = " [default: {}]".format(default) if default is not None else ""
        raw = input("\n  >> {}{}: ".format(prompt, suffix)).strip()

        if raw == "" and default is not None:
            return float(default)

        try:
            val = float(raw)
        except ValueError:
            print("    [!] Please enter a valid number.")
            continue

        if min_val is not None and val < min_val:
            print("    [!] Value must be >= {}. Try again.".format(min_val))
            continue
        if max_val is not None and val > max_val:
            print("    [!] Value must be <= {}. Try again.".format(max_val))
            continue

        return val


# =============================================================================
#  STEP 1 -- FETCH COMPANY DATA FROM YAHOO FINANCE
# =============================================================================

def fetch_company_data(ticker):
    """
    Pull key financial data automatically from Yahoo Finance.
    Returns a dictionary of company metrics used throughout the model.
    """
    stock = yf.Ticker(ticker)
    info  = stock.info

    # Calculate Free Cash Flow history: Operating CF minus CapEx
    fcf_list = []
    try:
        cf = stock.cashflow
        if "Operating Cash Flow" in cf.index and "Capital Expenditure" in cf.index:
            op_cf = cf.loc["Operating Cash Flow"].dropna()
            capex = cf.loc["Capital Expenditure"].dropna()
            for col in op_cf.index:
                if col in capex.index:
                    fcf_list.append(float(op_cf[col]) - float(capex[col]))
    except Exception:
        pass  # FCF not always available; handled gracefully below

    data = {
        "name"         : info.get("longName", ticker),
        "sector"       : info.get("sector", "N/A"),
        "industry"     : info.get("industry", "N/A"),
        "currency"     : info.get("currency", "USD"),
        "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
        "shares_out"   : info.get("sharesOutstanding"),
        "market_cap"   : info.get("marketCap"),
        "pe_ratio"     : info.get("trailingPE"),
        "revenue_ttm"  : info.get("totalRevenue"),
        "ebitda"       : info.get("ebitda"),
        "net_income"   : info.get("netIncomeToCommon"),
        "total_debt"   : info.get("totalDebt", 0) or 0,
        "cash"         : info.get("totalCash", 0) or 0,
        "beta"         : info.get("beta"),
        "fcf_history"  : fcf_list,           # list, most recent year first
        "latest_fcf"   : fcf_list[0] if fcf_list else None,
        "analyst_growth": info.get("earningsGrowth") or info.get("revenueGrowth"),
    }
    return data


# =============================================================================
#  STEP 2 -- DISPLAY COMPANY SNAPSHOT
# =============================================================================

def display_snapshot(d):
    """Print a summary of auto-retrieved company data."""
    section("COMPANY SNAPSHOT  (Auto-retrieved from Yahoo Finance)")
    print("    Company   : {}".format(d["name"]))
    print("    Sector    : {}  |  Industry: {}".format(d["sector"], d["industry"]))
    print("    Currency  : {}".format(d["currency"]))

    if d["current_price"]:
        print("    Price     : ${:,.2f}".format(d["current_price"]))
    else:
        print("    Price     : N/A")

    if d["market_cap"]:
        print("    Market Cap: {}".format(fmt(d["market_cap"])))
    if d["pe_ratio"]:
        print("    P/E Ratio : {:.1f}x".format(d["pe_ratio"]))
    if d["revenue_ttm"]:
        print("    Revenue   : {}".format(fmt(d["revenue_ttm"])))
    if d["ebitda"]:
        print("    EBITDA    : {}".format(fmt(d["ebitda"])))
    if d["net_income"]:
        print("    Net Income: {}".format(fmt(d["net_income"])))

    if d["fcf_history"]:
        print("\n    Free Cash Flow history (most recent first):")
        for i, fcf in enumerate(d["fcf_history"][:4]):
            label = "Latest" if i == 0 else "Year-{}".format(i)
            print("      {}: {}".format(label, fmt(fcf)))
    else:
        print("\n    [!] Free Cash Flow not available from Yahoo Finance.")
        print("        You will be asked to enter it manually below.")

    if d["beta"]:
        print("\n    Beta (market sensitivity): {:.2f}".format(d["beta"]))
    if d["analyst_growth"]:
        print("    Analyst Growth Estimate  : {:.1f}%".format(d["analyst_growth"] * 100))


# =============================================================================
#  STEP 3 -- COLLECT USER ASSUMPTIONS (interactive)
# =============================================================================

def collect_assumptions(d):
    """
    Walk the user through every DCF assumption, one at a time.
    Each input is preceded by an explanation of what it means and why it matters.
    Returns a dictionary of all assumptions.
    """
    section("YOUR VALUATION ASSUMPTIONS  (You provide these)")

    # ------------------------------------------------------------------
    # Base Free Cash Flow
    # ------------------------------------------------------------------
    explain(
        "BASE FREE CASH FLOW (FCF)\n"
        "FCF = Operating Cash Flow - Capital Expenditures.\n"
        "It represents the real cash a company generates after spending\n"
        "what it needs to maintain and grow its business.\n"
        "This is the foundation of the entire DCF model."
    )
    default_fcf = round(d["latest_fcf"] / 1e9, 2) if d["latest_fcf"] else None
    hint = " (auto-fetched: ${:.2f}B)".format(default_fcf) if default_fcf else " (not available -- enter manually)"
    base_fcf_b = get_float(
        "Base FCF in $ Billions{}".format(hint),
        default=default_fcf
    )
    base_fcf = base_fcf_b * 1e9

    # ------------------------------------------------------------------
    # Stage 1: High-growth phase
    # ------------------------------------------------------------------
    explain(
        "STAGE 1 GROWTH RATE\n"
        "How fast do you expect FCF to grow annually in the first phase?\n"
        "  - High-growth companies (tech, biotech): 15% - 30%\n"
        "  - Moderate-growth companies            :  8% - 15%\n"
        "  - Mature / slow-growth companies        :  2% -  8%\n"
        "Use analyst estimates, historical FCF growth, or your own view."
    )
    if d["analyst_growth"]:
        print("    [i] Analyst consensus growth estimate: {:.1f}%".format(d["analyst_growth"] * 100))

    g1 = get_float("Stage 1 Annual Growth Rate (%)", default=10.0, min_val=-50.0, max_val=100.0) / 100

    explain("STAGE 1 DURATION\nHow many years will the company sustain this high growth rate?")
    n1 = int(get_float("Stage 1 Duration (years)", default=5, min_val=1, max_val=20))

    # ------------------------------------------------------------------
    # Stage 2: Transition / slowdown phase
    # ------------------------------------------------------------------
    explain(
        "STAGE 2 GROWTH RATE  (Transition phase)\n"
        "Growth naturally slows as companies mature and competition increases.\n"
        "Stage 2 bridges the high-growth phase and the perpetual terminal rate.\n"
        "Typically ranges from 3% to 10%."
    )
    g2 = get_float("Stage 2 Annual Growth Rate (%)", default=5.0, min_val=-50.0, max_val=50.0) / 100

    explain("STAGE 2 DURATION\nHow many additional years for this transition phase?")
    n2 = int(get_float("Stage 2 Duration (years)", default=5, min_val=1, max_val=20))

    # ------------------------------------------------------------------
    # Terminal Growth Rate
    # ------------------------------------------------------------------
    explain(
        "TERMINAL GROWTH RATE\n"
        "After the projection period, we assume FCF grows at a CONSTANT rate\n"
        "FOREVER. This should reflect long-run nominal GDP growth.\n"
        "  - Typical range: 1.5% - 3.5%\n"
        "  - MUST be less than the discount rate (WACC), or the math breaks.\n"
        "  - Setting it too high inflates intrinsic value significantly."
    )
    g_term = get_float("Terminal Growth Rate (%)", default=2.5, min_val=0.0, max_val=6.0) / 100

    # ------------------------------------------------------------------
    # Discount Rate (WACC)
    # ------------------------------------------------------------------
    explain(
        "DISCOUNT RATE  (WACC -- Weighted Average Cost of Capital)\n"
        "This converts future cash flows into today's dollars.\n"
        "A higher rate means more risk = lower intrinsic value.\n"
        "\n"
        "How to estimate WACC (simplified CAPM approach):\n"
        "  WACC ~ Risk-Free Rate + Beta x Equity Risk Premium\n"
        "  Risk-Free Rate ~ 10-yr Treasury yield (~4.5% in 2025)\n"
        "  Equity Risk Premium (ERP) ~ 5% - 6% (long-run US average)\n"
        "\n"
        "  Guidelines:\n"
        "    8% - 10%  : low-risk, stable companies\n"
        "   10% - 12%  : average risk\n"
        "   12% - 15%  : higher risk or volatile sector\n"
        "   15%+       : very high risk / speculative"
    )
    if d["beta"]:
        implied_wacc = round(4.5 + d["beta"] * 5.5, 1)
        print("    [i] Beta = {:.2f}  =>  Rough CAPM WACC estimate: ~{}%".format(
            d["beta"], implied_wacc))
        print("        (Risk-free 4.5% + {:.2f} x 5.5% ERP)".format(d["beta"]))

    wacc = get_float("Discount Rate / WACC (%)", default=10.0, min_val=1.0, max_val=40.0) / 100

    # ------------------------------------------------------------------
    # Net Debt
    # ------------------------------------------------------------------
    net_debt = d["total_debt"] - d["cash"]
    explain(
        "NET DEBT\n"
        "Net Debt = Total Debt - Cash & Equivalents.\n"
        "We subtract this from Enterprise Value to get Equity Value.\n"
        "If a company has more cash than debt, Net Debt is negative\n"
        "(which ADDS to equity value -- a good thing for shareholders).\n"
        "\n"
        "Auto-fetched:\n"
        "  Total Debt  : {}\n"
        "  Cash        : {}\n"
        "  Net Debt    : {}".format(
            fmt(d["total_debt"]), fmt(d["cash"]), fmt(net_debt))
    )
    override = input("\n  >> Override Net Debt? (y/n) [n]: ").strip().lower()
    if override == "y":
        net_debt = get_float("Net Debt in $ Billions") * 1e9

    # ------------------------------------------------------------------
    # Shares Outstanding
    # ------------------------------------------------------------------
    shares = d["shares_out"] or 1e9
    explain(
        "SHARES OUTSTANDING\n"
        "Divides total Equity Value into a per-share intrinsic value.\n"
        "Auto-fetched: {:.2f}B shares.".format(shares / 1e9)
    )
    override2 = input("\n  >> Override Shares Outstanding? (y/n) [n]: ").strip().lower()
    if override2 == "y":
        shares = get_float("Shares Outstanding in Billions") * 1e9

    # ------------------------------------------------------------------
    # Margin of Safety
    # ------------------------------------------------------------------
    explain(
        "MARGIN OF SAFETY  (Benjamin Graham concept)\n"
        "Even a good DCF model has estimation errors.\n"
        "The Margin of Safety is a discount applied to your intrinsic value\n"
        "to protect against mistakes and unforeseen risks.\n"
        "\n"
        "  Example: Intrinsic Value = $100, MOS = 25%\n"
        "           Buy price target = $75\n"
        "\n"
        "  Conservative investors: 30% - 40%\n"
        "  Moderate investors    : 20% - 30%\n"
        "  Aggressive investors  : 10% - 20%"
    )
    mos = get_float("Margin of Safety (%)", default=25.0, min_val=0.0, max_val=70.0) / 100

    return {
        "base_fcf" : base_fcf,
        "g1"       : g1,  "n1": n1,
        "g2"       : g2,  "n2": n2,
        "g_term"   : g_term,
        "wacc"     : wacc,
        "net_debt" : net_debt,
        "shares"   : shares,
        "mos"      : mos,
    }


# =============================================================================
#  STEP 4 -- RUN THE DCF MODEL
# =============================================================================

def run_dcf(a):
    """
    Two-stage DCF model with Gordon Growth Model terminal value.

    Stage 1: FCF grows at g1 for n1 years.
    Stage 2: FCF grows at g2 for n2 years.
    Terminal: Gordon Growth Model applied to year-(n1+n2) FCF.

    Each year's FCF is discounted at WACC back to present value.
    """
    base_fcf = a["base_fcf"]
    wacc     = a["wacc"]
    g_term   = a["g_term"]

    projected_fcfs = []   # list of (year, fcf, pv)
    cumulative_pv  = 0.0
    year           = 0
    current_fcf    = base_fcf

    # --- Stage 1 ---
    for _ in range(a["n1"]):
        year        += 1
        current_fcf *= (1 + a["g1"])
        pv           = current_fcf / (1 + wacc) ** year
        projected_fcfs.append((year, current_fcf, pv))
        cumulative_pv += pv

    # --- Stage 2 ---
    for _ in range(a["n2"]):
        year        += 1
        current_fcf *= (1 + a["g2"])
        pv           = current_fcf / (1 + wacc) ** year
        projected_fcfs.append((year, current_fcf, pv))
        cumulative_pv += pv

    # --- Terminal Value (Gordon Growth Model) ---
    terminal_fcf   = current_fcf * (1 + g_term)
    terminal_value = terminal_fcf / (wacc - g_term)
    pv_terminal    = terminal_value / (1 + wacc) ** year

    # --- Bridge to per-share value ---
    enterprise_value    = cumulative_pv + pv_terminal
    equity_value        = enterprise_value - a["net_debt"]
    intrinsic_per_share = equity_value / a["shares"] if a["shares"] else 0
    mos_price           = intrinsic_per_share * (1 - a["mos"])

    return {
        "projected_fcfs"     : projected_fcfs,
        "cumulative_pv"      : cumulative_pv,
        "terminal_value"     : terminal_value,
        "pv_terminal"        : pv_terminal,
        "enterprise_value"   : enterprise_value,
        "equity_value"       : equity_value,
        "intrinsic_per_share": intrinsic_per_share,
        "mos_price"          : mos_price,
        "total_years"        : year,
    }


# =============================================================================
#  STEP 5 -- DISPLAY RESULTS  (step-by-step breakdown)
# =============================================================================

def display_results(r, a, d):
    """Print the full model output with explanations at each stage."""

    # --- FCF Projection Table ---
    section("STEP-BY-STEP DCF BREAKDOWN")
    explain(
        "Each projected FCF is discounted to present value using WACC.\n"
        "Formula: PV = FCF_year / (1 + WACC)^year\n"
        "A dollar received in the future is worth less than a dollar today."
    )
    print("\n    {:<6} {:<22} {:<22} {}".format(
        "Year", "Projected FCF", "Present Value", "Stage"))
    print("    " + "-" * 58)
    for (yr, fcf, pv) in r["projected_fcfs"]:
        stage = "Stage 1" if yr <= a["n1"] else "Stage 2"
        print("    {:<6} {:<22} {:<22} {}".format(
            yr, fmt(fcf), fmt(pv), stage))

    print("\n    Sum of PV (Projection Period): {}".format(fmt(r["cumulative_pv"])))

    # --- Terminal Value ---
    section("TERMINAL VALUE")
    explain(
        "Terminal Value (TV) captures ALL cash flows BEYOND the projection period.\n"
        "\n"
        "Formula (Gordon Growth Model):\n"
        "  TV = FCF_last_year x (1 + g_terminal) / (WACC - g_terminal)\n"
        "\n"
        "  TV = {} x (1 + {:.1f}%) / ({:.1f}% - {:.1f}%)\n"
        "\n"
        "TV is then discounted back {} years to get its present value.\n"
        "TV often represents 50-80% of total intrinsic value -- which is\n"
        "why the terminal growth rate assumption is so critical.".format(
            fmt(a["base_fcf"]),
            a["g_term"] * 100,
            a["wacc"] * 100,
            a["g_term"] * 100,
            r["total_years"]
        )
    )
    tv_pct = r["pv_terminal"] / r["enterprise_value"] * 100
    print("\n    Terminal Value (undiscounted) : {}".format(fmt(r["terminal_value"])))
    print("    PV of Terminal Value          : {}".format(fmt(r["pv_terminal"])))
    print("    Terminal Value as % of EV     : {:.1f}%".format(tv_pct))
    if tv_pct > 80:
        print("\n    [!] WARNING: TV > 80% of Enterprise Value.")
        print("        Your result is very sensitive to WACC and terminal growth rate.")
        print("        Small changes in these inputs will dramatically change intrinsic value.")

    # --- Valuation Bridge ---
    section("VALUATION BRIDGE")
    explain(
        "Enterprise Value = PV of projected FCFs + PV of Terminal Value\n"
        "Equity Value     = Enterprise Value - Net Debt\n"
        "                   (subtract debt, add back excess cash)\n"
        "Intrinsic Value  = Equity Value / Shares Outstanding"
    )
    print("\n    PV of Projected FCFs          : {}".format(fmt(r["cumulative_pv"])))
    print("    (+) PV of Terminal Value      : {}".format(fmt(r["pv_terminal"])))
    print("    " + "-" * 45)
    print("    Enterprise Value              : {}".format(fmt(r["enterprise_value"])))
    print("    (-) Net Debt                  : {}".format(fmt(a["net_debt"])))
    print("    " + "-" * 45)
    print("    Equity Value                  : {}".format(fmt(r["equity_value"])))
    print("    Shares Outstanding            : {:.2f}B".format(a["shares"] / 1e9))
    print("    " + "-" * 45)
    print("    Intrinsic Value per Share     : ${:,.2f}".format(r["intrinsic_per_share"]))

    # --- Final Verdict ---
    section("INTRINSIC VALUE vs. MARKET PRICE")
    iv = r["intrinsic_per_share"]
    mos_price = r["mos_price"]
    mp = d["current_price"]

    print("\n    Intrinsic Value per Share     : ${:,.2f}".format(iv))
    print("    Margin of Safety ({:.0f}%) Price  : ${:,.2f}".format(a["mos"] * 100, mos_price))

    if mp:
        print("    Current Market Price          : ${:,.2f}".format(mp))
        upside = (iv - mp) / mp * 100
        print("\n    Upside / (Downside) to IV     : {:+.1f}%".format(upside))
        print()

        if mp <= mos_price:
            verdict = "[BUY ZONE]  Price is BELOW your margin-of-safety target. Potentially undervalued."
        elif mp <= iv:
            verdict = "[WATCH]     Price is below intrinsic value but above MOS target. Fairly valued."
        else:
            verdict = "[CAUTION]   Price EXCEEDS estimated intrinsic value. Potentially overvalued."

        print("    >>> {}".format(verdict))
    else:
        print("    Current Market Price : N/A")

    # --- Sensitivity Table ---
    section("SENSITIVITY ANALYSIS  (Intrinsic Value per Share)")
    explain(
        "DCF results are highly sensitive to WACC and terminal growth rate.\n"
        "This table shows how intrinsic value changes as you vary those two inputs.\n"
        "Look for the cell matching your base assumptions -- then see how much\n"
        "the result changes if you are slightly wrong on either input."
    )

    wacc_offsets  = [-0.02, -0.01, 0.0, +0.01, +0.02]
    gterm_offsets = [-0.01, 0.0, +0.01]

    wacc_range  = [a["wacc"]   + dx for dx in wacc_offsets]
    gterm_range = [a["g_term"] + dg for dg in gterm_offsets]

    col_w = 14
    header_row = "    {:<14}".format("WACC \\ g_term")
    for g in gterm_range:
        label = "g={:.1f}%".format(g * 100)
        header_row += "{:>{}}".format(label, col_w)
    print("\n" + header_row)
    print("    " + "-" * (14 + col_w * len(gterm_range)))

    for w in wacc_range:
        if w <= 0:
            continue
        row_label = "WACC={:.1f}%".format(w * 100)
        is_base_wacc = abs(w - a["wacc"]) < 0.001
        row = "    {:<14}".format(row_label)
        for g in gterm_range:
            if g <= 0 or w <= g:
                row += "{:>{}}".format("N/A", col_w)
                continue
            temp_r  = run_dcf({**a, "wacc": w, "g_term": g})
            iv_sens = temp_r["intrinsic_per_share"]
            is_base = is_base_wacc and abs(g - a["g_term"]) < 0.001
            cell    = "${:,.0f}{}".format(iv_sens, "*" if is_base else "")
            row += "{:>{}}".format(cell, col_w)
        print(row)

    print("\n    * = your base-case assumptions")

    # --- Disclaimer ---
    section("IMPORTANT DISCLAIMER")
    print("    This is an educational tool designed to teach DCF concepts.")
    print("    All projections are estimates based on user-provided assumptions.")
    print("    This output is NOT financial advice.")
    print("    Always conduct thorough independent research before investing.")


# =============================================================================
#  MAIN FUNCTION
# =============================================================================

def main():
    """
    Entry point for the DCF Valuation Calculator.

    HOW TO RUN IN SPYDER:
      - Press F5 to run the file (main() is called automatically at the bottom).
      - Or type  main()  in the IPython console at any time to restart.
    """
    header("DCF INTRINSIC VALUE CALCULATOR")
    print("  A step-by-step Discounted Cash Flow valuation model.")
    print("  Data is fetched from Yahoo Finance. You provide the assumptions.")
    print("  Each input has a detailed explanation to guide your thinking.")

    # ------------------------------------------------------------------
    # Step 1: Ticker input
    # ------------------------------------------------------------------
    section("STEP 1 -- ENTER STOCK TICKER")
    explain(
        "Enter the ticker symbol of the stock you want to value.\n"
        "Examples: AAPL (Apple), MSFT (Microsoft), GOOGL (Alphabet), JPM (JPMorgan)"
    )

    while True:
        ticker = input("\n  >> Ticker: ").strip().upper()
        if not ticker:
            print("    [!] Please enter a ticker symbol.")
            continue
        print("\n  Fetching data for {} from Yahoo Finance...".format(ticker))
        try:
            data = fetch_company_data(ticker)
            if not data["current_price"]:
                print("    [!] Could not retrieve price data for '{}'.".format(ticker))
                print("        Check the ticker symbol and try again.")
                continue
            print("  Done.")
            break
        except Exception as e:
            print("    [!] Error: {}".format(e))
            print("        Please check your internet connection or try a different ticker.")

    display_snapshot(data)

    # ------------------------------------------------------------------
    # Step 2: User assumptions
    # ------------------------------------------------------------------
    section("STEP 2 -- ENTER VALUATION ASSUMPTIONS")
    explain(
        "You will now enter your assumptions one at a time.\n"
        "Each input is preceded by an explanation of what it means and\n"
        "how it affects the model. Press Enter to accept the default value."
    )
    assumptions = collect_assumptions(data)

    # Guard: WACC must exceed terminal growth
    if assumptions["wacc"] <= assumptions["g_term"]:
        print("\n  [!] WACC must be greater than the terminal growth rate.")
        print("      Automatically adjusting terminal growth to WACC - 1%.")
        assumptions["g_term"] = assumptions["wacc"] - 0.01

    # ------------------------------------------------------------------
    # Step 3: Run the model
    # ------------------------------------------------------------------
    section("STEP 3 -- RUNNING DCF MODEL")
    print("  Calculating projected cash flows and present values...")
    results = run_dcf(assumptions)
    print("  Done.")

    # ------------------------------------------------------------------
    # Step 4: Display full breakdown
    # ------------------------------------------------------------------
    display_results(results, assumptions, data)

    # ------------------------------------------------------------------
    # Optional: Save to file
    # ------------------------------------------------------------------
    print()
    save = input("\n  >> Save results to a text file? (y/n) [n]: ").strip().lower()
    if save == "y":
        fname = "DCF_{}_results.txt".format(ticker)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            display_results(results, assumptions, data)
        with open(fname, "w", encoding="utf-8") as f:
            f.write(buf.getvalue())
        print("  Results saved to: {}".format(fname))

    header("VALUATION COMPLETE -- Thank you for using the DCF Calculator")
    print("  To run again, type  main()  in the IPython console.\n")


# =============================================================================
#  AUTO-RUN
#  In Spyder, pressing F5 executes the whole file -- this line ensures
#  main() is called regardless of whether __name__ == "__main__" is True.
#  (In Spyder's IPython kernel, __name__ is often '__main__' only sometimes.)
# =============================================================================
main()
