#!/usr/bin/env python3
"""
Diesel Fuel Consumption Prediction Model

Predicts UK diesel car fuel consumption based on:
- Fleet size (new sales - scrapped vehicles)
- Annual mileage by vehicle age
- Average fuel economy

Uses MOT-derived survival curves and mileage data combined with
external sales and consumption statistics.

Usage:
    python diesel_prediction.py                    # Run full prediction
    python diesel_prediction.py --backtest         # Validate against historical
    python diesel_prediction.py --forecast 2035    # Project to specific year
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent directory to path for lib imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Data paths
DATA_DIR = Path('/Volumes/T7/MOT/data/diesel_external')


# ============================================================================
# SURVIVAL CURVES (from MOT analysis)
# ============================================================================

# Survival rates by vehicle age (from diesel_analysis.py --survival)
# Based on 2024-2025 MOT data for vehicles registered 2005-2020
# Ages 0-4 are estimated (vehicles under 3 don't need MOT)
# Ages 5+ are from actual MOT data
# FIX: Added ages 0-2, corrected age 3-4 to be monotonically decreasing
SURVIVAL_RATES = {
    0: 1.000,  # New vehicle
    1: 0.998,  # Estimated - very few losses in first year
    2: 0.995,  # Estimated - slight attrition
    3: 0.990,  # First MOT due, estimated
    4: 0.987,  # Estimated (must be > age 5)
    5: 0.983,  # From MOT data
    6: 0.971,
    7: 0.958,
    8: 0.944,
    9: 0.931,
    10: 0.912,
    11: 0.885,
    12: 0.851,
    13: 0.803,
    14: 0.731,
    15: 0.659,
    16: 0.569,
    17: 0.434,
    18: 0.345,
    19: 0.256,
    20: 0.184,
    21: 0.130,
    22: 0.090,
    23: 0.060,
    24: 0.035,
    25: 0.020,
}


# ============================================================================
# ANNUAL MILEAGE BY AGE (from MOT analysis)
# ============================================================================

# Median annual miles by vehicle age (from diesel_analysis.py --mileage)
# Ages 0-2 estimated from industry data (new cars driven more)
ANNUAL_MILEAGE_BY_AGE = {
    0: 12000,  # New car - estimated high usage
    1: 11800,  # Estimated
    2: 11700,  # Estimated
    3: 11617,
    4: 9769,
    5: 9344,
    6: 8977,
    7: 8625,
    8: 8286,
    9: 7923,
    10: 7594,
    11: 7266,
    12: 6959,
    13: 6647,
    14: 6284,
    15: 6015,
    16: 5644,
    17: 5328,
    18: 4946,
    19: 4514,
    20: 4151,
    21: 3800,  # extrapolated
    22: 3500,
    23: 3200,
    24: 2900,
    25: 2600,
}


# ============================================================================
# FUEL ECONOMY
# ============================================================================

# Average diesel MPG (UK gallons) - varies by vehicle age
# Older vehicles are less efficient, newer ones better
DIESEL_MPG_BY_AGE = {
    0: 55,   # Modern efficient diesels (Euro 6d)
    1: 55,
    2: 55,
    3: 55,
    4: 54,
    5: 53,
    6: 52,
    7: 51,
    8: 50,
    9: 49,
    10: 48,
    11: 47,
    12: 46,
    13: 45,
    14: 44,
    15: 43,
    16: 42,
    17: 41,
    18: 40,
    19: 39,
    20: 38,
    21: 37,
    22: 36,
    23: 35,
    24: 34,
    25: 33,
}


def load_external_data():
    """Load external CSV data files."""
    data = {}

    # Car sales
    try:
        df = pd.read_csv(DATA_DIR / 'car_sales.csv', comment='#')
        data['car_sales'] = df.set_index('year')
    except Exception as e:
        print(f"Warning: Could not load car_sales.csv: {e}")

    # Fleet size
    try:
        df = pd.read_csv(DATA_DIR / 'fleet_size.csv', comment='#')
        data['fleet_size'] = df.set_index('year')
    except Exception as e:
        print(f"Warning: Could not load fleet_size.csv: {e}")

    # Fuel consumption
    try:
        df = pd.read_csv(DATA_DIR / 'fuel_consumption.csv', comment='#')
        data['fuel_consumption'] = df.set_index('year')
    except Exception as e:
        print(f"Warning: Could not load fuel_consumption.csv: {e}")

    # Van sales
    try:
        df = pd.read_csv(DATA_DIR / 'van_sales.csv', comment='#')
        data['van_sales'] = df.set_index('year')
    except Exception as e:
        print(f"Warning: Could not load van_sales.csv: {e}")

    return data


def build_fleet_model(data: dict, base_year: int = 2010, forecast_year: int = 2035):
    """
    Build a fleet model from historical sales and survival curves.

    For each year, tracks vehicles by registration year cohort.
    """
    print(f"\nBuilding fleet model from {base_year} to {forecast_year}...")

    car_sales = data.get('car_sales')
    if car_sales is None:
        raise ValueError("Car sales data required")

    # Initialize fleet structure: {year: {reg_year: vehicle_count}}
    fleet = {}

    for year in range(base_year, forecast_year + 1):
        fleet[year] = {}

        # For each cohort (vehicles registered in each year)
        for reg_year in range(1995, year + 1):
            age = year - reg_year

            # Skip very old vehicles or those not yet registered
            # FIX: Include ages 0-2 (new vehicles also consume fuel)
            if age < 0 or age > 25:
                continue

            # Get new registrations for this cohort
            if reg_year in car_sales.index:
                new_cars = car_sales.loc[reg_year, 'diesel_new_cars']
            else:
                # Extrapolate based on trend
                if reg_year > car_sales.index.max():
                    # Future: declining trend
                    last_year = car_sales.index.max()
                    decline_rate = 0.85  # 15% decline per year
                    years_ahead = reg_year - last_year
                    new_cars = car_sales.loc[last_year, 'diesel_new_cars'] * (decline_rate ** years_ahead)
                else:
                    continue

            # Apply survival rate
            survival = SURVIVAL_RATES.get(age, 0)
            surviving = int(new_cars * survival)

            if surviving > 0:
                fleet[year][reg_year] = surviving

    return fleet


def calculate_consumption(fleet: dict, mileage_adjustment: float = 1.0):
    """
    Calculate annual diesel consumption from fleet model.

    Args:
        fleet: {year: {reg_year: vehicle_count}}
        mileage_adjustment: Factor to adjust mileage (e.g., 0.9 for -10%)

    Returns:
        DataFrame with year, fleet_size, total_miles, litres_consumed
    """
    results = []

    for year, cohorts in sorted(fleet.items()):
        total_vehicles = 0
        total_miles = 0
        total_litres = 0

        for reg_year, count in cohorts.items():
            age = year - reg_year

            # Get annual mileage for this age
            annual_miles = ANNUAL_MILEAGE_BY_AGE.get(age, 4000) * mileage_adjustment

            # Get fuel economy
            mpg = DIESEL_MPG_BY_AGE.get(age, 40)

            # Calculate
            miles = count * annual_miles
            # Litres = miles / mpg * 4.546 (UK gallon in litres)
            litres = miles / mpg * 4.546

            total_vehicles += count
            total_miles += miles
            total_litres += litres

        results.append({
            'year': year,
            'fleet_size_millions': total_vehicles / 1_000_000,
            'total_miles_billions': total_miles / 1_000_000_000,
            'car_litres_billions': total_litres / 1_000_000_000,
        })

    return pd.DataFrame(results)


def estimate_van_consumption(data: dict, years: list):
    """
    Estimate diesel van consumption based on SMMT data.

    Vans typically drive ~12,000 miles/year at ~35 MPG.
    """
    van_sales = data.get('van_sales')
    if van_sales is None:
        print("Warning: No van sales data, estimating conservatively")
        # Rough estimate: vans are ~40% of car consumption
        return None

    results = []
    # Assume van fleet is ~4M and growing slowly
    van_fleet = 4_000_000
    van_annual_miles = 12000
    van_mpg = 35

    for year in years:
        # Van fleet growth/decline based on sales
        if year in van_sales.index:
            diesel_vans_sold = van_sales.loc[year, 'diesel_lcv']
            # Rough survival: assume 8% scrapped per year
            van_fleet = van_fleet * 0.92 + diesel_vans_sold

        miles = van_fleet * van_annual_miles
        litres = miles / van_mpg * 4.546

        results.append({
            'year': year,
            'van_fleet_millions': van_fleet / 1_000_000,
            'van_litres_billions': litres / 1_000_000_000,
        })

    return pd.DataFrame(results)


def backtest(data: dict, start_year: int = 2015, end_year: int = 2024):
    """Compare predictions with actual fuel consumption data."""
    print("\n" + "=" * 70)
    print("BACKTEST: Comparing predicted vs actual diesel consumption")
    print("=" * 70)

    # Build fleet and calculate consumption
    fleet = build_fleet_model(data, base_year=start_year, forecast_year=end_year)
    car_consumption = calculate_consumption(fleet)
    van_consumption = estimate_van_consumption(data, list(range(start_year, end_year + 1)))

    # Get actual consumption
    actual = data.get('fuel_consumption')

    print(f"\n{'Year':<6} {'Car Litres':>12} {'Van Litres':>12} {'Total Pred':>12} {'Actual':>12} {'Error':>10}")
    print("-" * 70)

    for _, row in car_consumption.iterrows():
        year = int(row['year'])
        car_l = row['car_litres_billions']

        van_l = 0
        if van_consumption is not None:
            van_row = van_consumption[van_consumption['year'] == year]
            if len(van_row) > 0:
                van_l = van_row.iloc[0]['van_litres_billions']

        total_pred = car_l + van_l

        # Note: Total road diesel includes HGVs, buses - we're only predicting cars+vans
        # Cars+vans are roughly 55-60% of total diesel consumption
        actual_val = None
        error = None
        if actual is not None and year in actual.index:
            actual_val = actual.loc[year, 'diesel_billion_litres']
            # Estimate car+van share at ~55%
            car_van_actual = actual_val * 0.55
            error = ((total_pred - car_van_actual) / car_van_actual) * 100

        actual_str = f"{actual_val:.1f}" if actual_val else "N/A"
        error_str = f"{error:+.1f}%" if error else "N/A"

        print(f"{year:<6} {car_l:>12.2f} {van_l:>12.2f} {total_pred:>12.2f} {actual_str:>12} {error_str:>10}")

    print("-" * 70)
    print("Note: Actual is total road diesel; cars+vans are ~55% of this")


def forecast(data: dict, target_year: int = 2035):
    """Project diesel consumption forward."""
    print("\n" + "=" * 70)
    print(f"FORECAST: Diesel car consumption to {target_year}")
    print("=" * 70)

    fleet = build_fleet_model(data, base_year=2020, forecast_year=target_year)
    consumption = calculate_consumption(fleet)

    # Also model with declining mileage trend (diesels being driven less)
    consumption_declining = calculate_consumption(fleet, mileage_adjustment=0.98)  # 2% less per year cumulative

    print(f"\n{'Year':<6} {'Fleet (M)':>12} {'Miles (B)':>12} {'Litres (B)':>14} {'vs 2024':>10}")
    print("-" * 65)

    base_litres = None
    for _, row in consumption.iterrows():
        year = int(row['year'])
        fleet_m = row['fleet_size_millions']
        miles_b = row['total_miles_billions']
        litres_b = row['car_litres_billions']

        if year == 2024:
            base_litres = litres_b

        change = ""
        if base_litres and year >= 2024:
            pct_change = ((litres_b - base_litres) / base_litres) * 100
            change = f"{pct_change:+.0f}%"

        print(f"{year:<6} {fleet_m:>12.2f} {miles_b:>12.1f} {litres_b:>14.2f} {change:>10}")

    print("-" * 65)

    # Summary
    print("\nKey projections:")
    row_2030 = consumption[consumption['year'] == 2030].iloc[0]
    row_2035 = consumption[consumption['year'] == 2035].iloc[0] if target_year >= 2035 else None

    print(f"  2030: {row_2030['fleet_size_millions']:.1f}M vehicles, {row_2030['car_litres_billions']:.1f}B litres")
    if row_2035 is not None:
        print(f"  2035: {row_2035['fleet_size_millions']:.1f}M vehicles, {row_2035['car_litres_billions']:.1f}B litres")


def summary(data: dict):
    """Print summary of available data."""
    print("\n" + "=" * 70)
    print("DIESEL PREDICTION MODEL - DATA SUMMARY")
    print("=" * 70)

    print("\n1. CAR SALES DATA")
    if 'car_sales' in data:
        df = data['car_sales']
        print(f"   Years: {df.index.min()} - {df.index.max()}")
        latest = df.index.max()
        print(f"   Latest ({latest}): {df.loc[latest, 'diesel_new_cars']:,.0f} diesel cars ({df.loc[latest, 'diesel_share']:.1f}% share)")
    else:
        print("   NOT AVAILABLE")

    print("\n2. FLEET SIZE DATA")
    if 'fleet_size' in data:
        df = data['fleet_size']
        print(f"   Years: {df.index.min()} - {df.index.max()}")
        latest = df.index.max()
        print(f"   Latest ({latest}): {df.loc[latest, 'diesel_cars_millions']:.1f}M diesel cars")
    else:
        print("   NOT AVAILABLE")

    print("\n3. FUEL CONSUMPTION DATA")
    if 'fuel_consumption' in data:
        df = data['fuel_consumption']
        print(f"   Years: {df.index.min()} - {df.index.max()}")
        latest = df.index.max()
        print(f"   Latest ({latest}): {df.loc[latest, 'diesel_billion_litres']:.1f}B litres")
        peak = df['diesel_billion_litres'].max()
        peak_year = df['diesel_billion_litres'].idxmax()
        print(f"   Peak: {peak:.1f}B litres in {peak_year}")
    else:
        print("   NOT AVAILABLE")

    print("\n4. VAN SALES DATA")
    if 'van_sales' in data:
        df = data['van_sales']
        print(f"   Years: {df.index.min()} - {df.index.max()}")
        latest = df.index.max()
        print(f"   Latest ({latest}): {df.loc[latest, 'diesel_lcv']:,.0f} diesel LCVs ({df.loc[latest, 'diesel_share']:.1f}% share)")
    else:
        print("   NOT AVAILABLE")

    print("\n5. MOT-DERIVED PARAMETERS")
    print("   Survival rates: 20-year range (18.4% at age 20, 98.3% at age 5)")
    print("   Annual mileage: 11,617 mi (age 3) declining to 4,151 mi (age 20)")
    print("   Fuel economy: 55 MPG (new) declining to 33 MPG (age 25)")


def main():
    parser = argparse.ArgumentParser(description='Diesel fuel consumption prediction')
    parser.add_argument('--backtest', action='store_true', help='Validate against historical data')
    parser.add_argument('--forecast', type=int, default=None, help='Project to specific year (default: 2035)')
    parser.add_argument('--summary', action='store_true', help='Show data summary')

    args = parser.parse_args()

    # Load data
    data = load_external_data()

    if args.summary or not (args.backtest or args.forecast):
        summary(data)

    if args.backtest:
        backtest(data)

    if args.forecast:
        forecast(data, target_year=args.forecast)
    elif not args.backtest and not args.summary:
        # Default: run forecast to 2035
        forecast(data, target_year=2035)

    print("\nDone.")


if __name__ == "__main__":
    main()
