#!/usr/bin/env python3
"""
Diesel vehicle analysis from MOT data.

Provides survival curves, mileage analysis, and fleet age distribution
for diesel passenger cars to support fuel consumption prediction.

Usage:
    python diesel_analysis.py --survival           # Vehicle survival rates
    python diesel_analysis.py --mileage            # Annual mileage by age
    python diesel_analysis.py --fleet              # Current fleet age distribution
    python diesel_analysis.py --trends             # Mileage trends over time
    python diesel_analysis.py --summary            # Quick diesel summary
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for lib imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.db import get_connection, get_table_pattern


def diesel_summary(con, pattern: str):
    """Quick summary of diesel vehicles in the dataset."""
    print("\nDiesel Vehicle Summary")
    print("=" * 60)

    # Total diesel vehicles and tests (filter out invalid dates)
    result = con.execute(f"""
        SELECT
            COUNT(*) as total_tests,
            COUNT(DISTINCT registration) as unique_vehicles,
            MIN(CASE WHEN YEAR(TRY_CAST(testDate AS DATE)) >= 2005 THEN testDate END) as earliest_test,
            MAX(testDate) as latest_test
        FROM read_parquet('{pattern}')
        WHERE UPPER(fuelType) = 'DIESEL'
    """).fetchone()

    print(f"Total diesel tests:     {result[0]:,}")
    print(f"Unique diesel vehicles: {result[1]:,}")
    print(f"Date range:             {str(result[2])[:10]} to {str(result[3])[:10]}")

    # Odometer coverage
    result = con.execute(f"""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN odometerResultType = 'READ' THEN 1 ELSE 0 END) as valid_odometer,
            AVG(CASE WHEN odometerResultType = 'READ' THEN odometerValue END) as avg_mileage,
            MEDIAN(CASE WHEN odometerResultType = 'READ' THEN odometerValue END) as median_mileage
        FROM read_parquet('{pattern}')
        WHERE UPPER(fuelType) = 'DIESEL'
    """).fetchone()

    pct_valid = 100.0 * result[1] / result[0] if result[0] > 0 else 0
    avg_mileage = result[2] if result[2] else 0
    median_mileage = result[3] if result[3] else 0
    print(f"\nOdometer coverage:      {pct_valid:.1f}%")
    print(f"Average mileage:        {avg_mileage:,.0f} miles")
    print(f"Median mileage:         {median_mileage:,.0f} miles")

    # Registration year distribution (sample)
    print("\nVehicles by registration year (top 10):")
    results = con.execute(f"""
        SELECT
            YEAR(TRY_CAST(firstUsedDate AS DATE)) as reg_year,
            COUNT(DISTINCT registration) as vehicles
        FROM read_parquet('{pattern}')
        WHERE UPPER(fuelType) = 'DIESEL'
          AND firstUsedDate IS NOT NULL
        GROUP BY reg_year
        HAVING reg_year >= 2005 AND reg_year <= 2025
        ORDER BY vehicles DESC
        LIMIT 10
    """).fetchall()

    for row in results:
        print(f"  {row[0]}: {row[1]:,} vehicles")


def survival_curve(con, pattern: str, min_year: int = 2005, max_year: int = 2020):
    """
    Calculate survival rates for diesel vehicles by registration year.

    Survival = vehicles with MOT in recent period / vehicles ever registered
    """
    # Get current year dynamically
    from datetime import datetime
    current_year = datetime.now().year
    recent_year = current_year - 1  # Look for tests in last 2 years

    print("\nDiesel Vehicle Survival Rates")
    print("=" * 70)
    print(f"(Vehicles registered {min_year}-{max_year}, tested in {recent_year}-{current_year})")
    print()

    # For each registration year, count:
    # 1. Vehicles with any MOT test (with valid odometer)
    # 2. Vehicles with recent MOT (same filter applied consistently)
    # FIX: Apply same odometerResultType filter to both CTEs to avoid survivorship bias
    query = f"""
        WITH diesel_vehicles AS (
            SELECT DISTINCT
                registration,
                YEAR(TRY_CAST(firstUsedDate AS DATE)) as reg_year
            FROM read_parquet('{pattern}')
            WHERE UPPER(fuelType) = 'DIESEL'
              AND odometerResultType = 'READ'
        ),
        recent_tests AS (
            SELECT DISTINCT registration
            FROM read_parquet('{pattern}')
            WHERE UPPER(fuelType) = 'DIESEL'
              AND odometerResultType = 'READ'
              AND YEAR(TRY_CAST(testDate AS DATE)) >= {recent_year}
        )
        SELECT
            d.reg_year,
            COUNT(DISTINCT d.registration) as total_registered,
            COUNT(DISTINCT r.registration) as still_active,
            {current_year} - d.reg_year as vehicle_age
        FROM diesel_vehicles d
        LEFT JOIN recent_tests r ON d.registration = r.registration
        WHERE d.reg_year >= {min_year} AND d.reg_year <= {max_year}
        GROUP BY d.reg_year
        ORDER BY d.reg_year
    """

    results = con.execute(query).fetchall()

    print(f"{'Reg Year':<10} {'Age':>5} {'Registered':>12} {'Active':>14} {'Survival %':>12}")
    print("-" * 70)

    for row in results:
        reg_year, total, active, age = row
        survival_pct = 100.0 * active / total if total > 0 else 0
        print(f"{reg_year:<10} {age:>5} {total:>12,} {active:>14,} {survival_pct:>11.1f}%")

    print("-" * 70)
    print(f"\nNote: 'Active' means passed an MOT in {recent_year}-{current_year}")


def annual_mileage_by_age(con, pattern: str, sample_pct: float = 10):
    """
    Calculate average annual mileage by vehicle age.

    Uses delta between consecutive MOT readings.
    """
    print("\nAnnual Mileage by Vehicle Age (Diesel)")
    print("=" * 60)
    print(f"(Based on {sample_pct}% sample of consecutive MOT readings)")
    print()

    # This query calculates mileage delta between consecutive tests
    # and groups by vehicle age at time of test
    query = f"""
        WITH ordered_tests AS (
            SELECT
                registration,
                testDate,
                odometerValue,
                YEAR(TRY_CAST(testDate AS DATE)) - YEAR(TRY_CAST(firstUsedDate AS DATE)) as vehicle_age,
                LAG(odometerValue) OVER (PARTITION BY registration ORDER BY testDate) as prev_mileage,
                LAG(testDate) OVER (PARTITION BY registration ORDER BY testDate) as prev_test_date
            FROM read_parquet('{pattern}')
            WHERE UPPER(fuelType) = 'DIESEL'
              AND odometerResultType = 'READ'
              AND odometerValue > 0
            USING SAMPLE {sample_pct} PERCENT (bernoulli)
        ),
        mileage_deltas AS (
            SELECT
                vehicle_age,
                odometerValue - prev_mileage as mileage_delta,
                DATEDIFF('day', TRY_CAST(prev_test_date AS DATE), TRY_CAST(testDate AS DATE)) as days_between
            FROM ordered_tests
            WHERE prev_mileage IS NOT NULL
              AND odometerValue > prev_mileage
              AND vehicle_age >= 3 AND vehicle_age <= 20
        )
        SELECT
            vehicle_age,
            COUNT(*) as samples,
            ROUND(AVG(mileage_delta * 365.0 / NULLIF(days_between, 0)), 0) as avg_annual_miles,
            ROUND(MEDIAN(mileage_delta * 365.0 / NULLIF(days_between, 0)), 0) as median_annual_miles
        FROM mileage_deltas
        WHERE days_between >= 300 AND days_between <= 450  -- ~1 year between tests
          AND mileage_delta > 0 AND mileage_delta < 50000  -- Reasonable range
        GROUP BY vehicle_age
        ORDER BY vehicle_age
    """

    results = con.execute(query).fetchall()

    print(f"{'Age':>5} {'Samples':>12} {'Avg Annual':>14} {'Median Annual':>15}")
    print("-" * 50)

    for row in results:
        age, samples, avg_miles, median_miles = row
        if avg_miles and median_miles:
            print(f"{age:>5} {samples:>12,} {avg_miles:>14,.0f} {median_miles:>15,.0f}")

    print("-" * 50)
    print("\nNote: Based on ~1 year gaps between consecutive MOT tests")


def fleet_age_distribution(con, pattern: str):
    """
    Count active diesel vehicles by registration year.

    'Active' means passed MOT in recent period.
    """
    from datetime import datetime
    current_year = datetime.now().year
    recent_year = current_year - 1

    print("\nActive Diesel Fleet Age Distribution")
    print("=" * 60)
    print(f"(Vehicles with MOT in {recent_year}-{current_year})")
    print()

    query = f"""
        SELECT
            YEAR(TRY_CAST(firstUsedDate AS DATE)) as reg_year,
            COUNT(DISTINCT registration) as active_vehicles,
            {current_year} - YEAR(TRY_CAST(firstUsedDate AS DATE)) as age
        FROM read_parquet('{pattern}')
        WHERE UPPER(fuelType) = 'DIESEL'
          AND YEAR(TRY_CAST(testDate AS DATE)) >= {recent_year}
          AND firstUsedDate IS NOT NULL
        GROUP BY reg_year
        HAVING reg_year >= 2000 AND reg_year <= {current_year - 3}
        ORDER BY reg_year DESC
    """

    results = con.execute(query).fetchall()

    total = sum(r[1] for r in results)

    print(f"{'Reg Year':<10} {'Age':>5} {'Active Vehicles':>16} {'% of Fleet':>12}")
    print("-" * 50)

    for row in results:
        reg_year, vehicles, age = row
        pct = 100.0 * vehicles / total if total > 0 else 0
        print(f"{reg_year:<10} {age:>5} {vehicles:>16,} {pct:>11.1f}%")

    print("-" * 50)
    print(f"{'Total':<10} {'':>5} {total:>16,}")


def mileage_trend_over_time(con, pattern: str):
    """
    Track how diesel mileage has changed over different test years.

    Shows whether diesels are being driven less now vs historically.
    """
    print("\nDiesel Mileage Trends Over Time")
    print("=" * 70)
    print("(Average mileage at test for vehicles of same age, by test year)")
    print()

    # Compare mileage for 5-year-old diesels across different test years
    query = f"""
        SELECT
            YEAR(TRY_CAST(testDate AS DATE)) as test_year,
            YEAR(TRY_CAST(testDate AS DATE)) - YEAR(TRY_CAST(firstUsedDate AS DATE)) as vehicle_age,
            COUNT(*) as tests,
            ROUND(AVG(odometerValue), 0) as avg_mileage,
            ROUND(MEDIAN(odometerValue), 0) as median_mileage
        FROM read_parquet('{pattern}')
        WHERE UPPER(fuelType) = 'DIESEL'
          AND odometerResultType = 'READ'
          AND odometerValue > 0 AND odometerValue < 500000
        GROUP BY test_year, vehicle_age
        HAVING vehicle_age IN (5, 10, 15)
           AND test_year >= 2015 AND test_year <= 2024
        ORDER BY vehicle_age, test_year
    """

    results = con.execute(query).fetchall()

    # Group by vehicle age for display
    ages = {5: [], 10: [], 15: []}
    for row in results:
        test_year, age, tests, avg, median = row
        if age in ages:
            ages[age].append((test_year, tests, avg, median))

    for age in [5, 10, 15]:
        print(f"\n{age}-year-old diesel vehicles:")
        print(f"{'Test Year':<12} {'Tests':>12} {'Avg Mileage':>14} {'Median':>12}")
        print("-" * 55)

        for test_year, tests, avg, median in ages[age]:
            if avg and median:
                print(f"{test_year:<12} {tests:>12,} {avg:>14,.0f} {median:>12,.0f}")

    print("\n" + "=" * 70)
    print("Interpretation: If mileage is falling for same-age vehicles,")
    print("diesels are being driven less than historically.")


def main():
    parser = argparse.ArgumentParser(description='Diesel vehicle analysis from MOT data')
    parser.add_argument('--survival', action='store_true', help='Show survival rates by registration year')
    parser.add_argument('--mileage', action='store_true', help='Show annual mileage by vehicle age')
    parser.add_argument('--fleet', action='store_true', help='Show current fleet age distribution')
    parser.add_argument('--trends', action='store_true', help='Show mileage trends over time')
    parser.add_argument('--summary', action='store_true', help='Quick diesel summary')
    parser.add_argument('--all', action='store_true', help='Run all analyses')

    args = parser.parse_args()

    # If no args specified, show summary
    if not any([args.survival, args.mileage, args.fleet, args.trends, args.summary, args.all]):
        args.summary = True

    con = get_connection()
    pattern = get_table_pattern('tests')

    print("Diesel Vehicle Analysis")
    print("Using:", pattern)

    if args.summary or args.all:
        diesel_summary(con, pattern)

    if args.survival or args.all:
        survival_curve(con, pattern)

    if args.mileage or args.all:
        annual_mileage_by_age(con, pattern)

    if args.fleet or args.all:
        fleet_age_distribution(con, pattern)

    if args.trends or args.all:
        mileage_trend_over_time(con, pattern)

    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()
