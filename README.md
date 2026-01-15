# The Decline of Diesel

An interactive data analysis of UK diesel vehicle trends, predicting when diesel fuel demand will become unsustainable.

**Live site:** [View the analysis](https://citi94.github.io/diesel-decline/)

## Key Findings

- **Diesel sales have collapsed**: From 47% of new cars (2016) to just 5.1% (2025)
- **Fleet is shrinking**: 3.7 million fewer diesel cars than 2019
- **Diesels driven less**: 17% fewer miles than a decade ago
- **By 2035**: Diesel consumption predicted to fall 74%
- **By 2040**: Only ~1 million diesel cars will remain

## Data Sources

| Source | Data Used |
|--------|-----------|
| DVSA MOT API | 760M test records, 26M unique diesel vehicles |
| SMMT | New vehicle registrations by fuel type |
| GOV.UK | Fuel consumption, vehicle licensing stats |
| DfT NTS | Average annual mileage by fuel type |

## Methodology

1. **Survival Rates**: Calculated from MOT data - what proportion of vehicles from each registration year are still on the road
2. **Annual Mileage**: Derived from consecutive MOT odometer readings
3. **Fleet Projection**: Historical sales × survival rates
4. **Consumption**: Fleet × mileage × fuel economy

Full methodology: [View detailed methodology](https://citi94.github.io/diesel-decline/data/methodology.html)

## Project Structure

```
diesel-decline/
├── index.html              # Main interactive page
├── css/
│   └── style.css           # Styling
├── js/
│   ├── charts.js           # Chart.js visualizations
│   └── explorer.js         # Interactive scenario explorer
├── data/
│   ├── methodology.html    # Detailed methodology
│   └── diesel-data.json    # Raw data for charts
├── scripts/
│   ├── diesel_analysis.py  # MOT data analysis
│   └── diesel_prediction.py # Prediction model
└── README.md
```

## Running the Analysis

The analysis scripts require Python 3.8+ and access to MOT data:

```bash
# Install dependencies
pip install duckdb pandas numpy

# Run MOT analysis
python scripts/diesel_analysis.py --all

# Run prediction model
python scripts/diesel_prediction.py --forecast 2040
```

## Local Development

To run the website locally:

```bash
# Simple Python server
python -m http.server 8000

# Then visit http://localhost:8000
```

## Data Quality Notes

- MOT data covers passenger cars only (MOT Class 4)
- Vans and HGVs are estimated separately
- Pre-2019 fleet sizes are estimates (2019 and 2024 confirmed by GOV.UK)
- Model validated against historical fuel consumption data (±15% accuracy)

## License

MIT License - feel free to use this analysis and data.

## Credits

- Data: DVSA, SMMT, GOV.UK, DfT
- Analysis: Built with Claude Code
- Visualizations: Chart.js
