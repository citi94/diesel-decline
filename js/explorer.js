// Interactive Explorer for Diesel Decline Predictions

// Base data (from our model)
const baseData = {
    years: [2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039, 2040],
    fleet: [9.65, 9.24, 8.77, 8.24, 7.67, 7.04, 6.36, 5.66, 4.93, 4.22, 3.55, 2.94, 2.42, 1.98, 1.61, 1.31, 1.07],
    consumption: [7.06, 6.65, 6.22, 5.75, 5.27, 4.76, 4.23, 3.70, 3.18, 2.68, 2.22, 1.82, 1.47, 1.20, 0.97, 0.80, 0.65]
};

// Initialize explorer chart
let explorerChart;
const explorerCtx = document.getElementById('explorerChart').getContext('2d');

function initExplorerChart() {
    explorerChart = new Chart(explorerCtx, {
        type: 'line',
        data: {
            labels: baseData.years,
            datasets: [
                {
                    label: 'Base Scenario',
                    data: [...baseData.consumption],
                    borderColor: '#718096',
                    backgroundColor: 'transparent',
                    borderDash: [5, 5],
                    tension: 0.3,
                    pointRadius: 0
                },
                {
                    label: 'Your Scenario',
                    data: [...baseData.consumption],
                    borderColor: '#ed8936',
                    backgroundColor: 'rgba(237, 137, 54, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                title: {
                    display: true,
                    text: 'Diesel Car Consumption Scenario (Billion Litres)',
                    font: { size: 16 }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 10,
                    title: {
                        display: true,
                        text: 'Billion Litres'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Year'
                    }
                }
            }
        }
    });
}

// Calculate adjusted scenario based on sliders
function calculateScenario(salesDecline, mileageChange, survivalBoost) {
    const adjustedConsumption = [];

    for (let i = 0; i < baseData.years.length; i++) {
        const year = baseData.years[i];
        const yearsFromBase = year - 2024;

        // Adjust for sales decline (affects fleet size going forward)
        // More decline = fewer new cars = faster fleet shrinkage
        const salesFactor = Math.pow(1 - (salesDecline - 15) / 100, yearsFromBase);

        // Adjust for mileage change (cumulative)
        const mileageFactor = Math.pow(1 + mileageChange / 100, yearsFromBase);

        // Adjust for survival rate (affects how many old cars remain)
        const survivalFactor = 1 + (survivalBoost / 100);

        // Combined effect
        let adjusted = baseData.consumption[i] * salesFactor * mileageFactor * survivalFactor;

        // Don't let it go negative or above starting point
        adjusted = Math.max(0.1, Math.min(adjusted, baseData.consumption[0] * 1.2));

        adjustedConsumption.push(adjusted);
    }

    return adjustedConsumption;
}

// Update chart and results
function updateExplorer() {
    const salesDecline = parseInt(document.getElementById('salesDecline').value);
    const mileageChange = parseInt(document.getElementById('mileageChange').value);
    const survivalBoost = parseInt(document.getElementById('survivalBoost').value);

    // Update labels
    document.getElementById('salesDeclineValue').textContent = salesDecline + '%';
    document.getElementById('mileageChangeValue').textContent = (mileageChange >= 0 ? '+' : '') + mileageChange + '%';
    document.getElementById('survivalBoostValue').textContent = (survivalBoost >= 0 ? '+' : '') + survivalBoost + '%';

    // Calculate new scenario
    const adjustedData = calculateScenario(salesDecline, mileageChange, survivalBoost);

    // Update chart
    explorerChart.data.datasets[1].data = adjustedData;
    explorerChart.update();

    // Update results
    const idx2030 = baseData.years.indexOf(2030);
    const idx2035 = baseData.years.indexOf(2035);

    document.getElementById('result2030').textContent = adjustedData[idx2030].toFixed(1) + 'B litres';
    document.getElementById('result2035').textContent = adjustedData[idx2035].toFixed(1) + 'B litres';
}

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    initExplorerChart();

    // Add event listeners
    document.getElementById('salesDecline').addEventListener('input', updateExplorer);
    document.getElementById('mileageChange').addEventListener('input', updateExplorer);
    document.getElementById('survivalBoost').addEventListener('input', updateExplorer);
});

console.log('Explorer initialized');
