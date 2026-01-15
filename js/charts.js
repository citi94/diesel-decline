// Chart.js configuration and data

// Common chart options
const commonOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
        legend: {
            position: 'bottom',
            labels: {
                padding: 20,
                font: { size: 12 }
            }
        }
    }
};

// Color palette
const colors = {
    primary: '#1a365d',
    primaryLight: '#2c5282',
    accent: '#ed8936',
    accentDark: '#c05621',
    success: '#48bb78',
    danger: '#f56565',
    grey: '#718096'
};

// ============================================================================
// 1. Sales Chart - Diesel share of new car sales
// ============================================================================
const salesCtx = document.getElementById('salesChart').getContext('2d');
new Chart(salesCtx, {
    type: 'bar',
    data: {
        labels: ['2005', '2007', '2009', '2011', '2013', '2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025'],
        datasets: [{
            label: 'Diesel Share of New Cars (%)',
            data: [22, 26, 28, 31.5, 36, 45, 47, 43, 30, 22, 16, 9, 8, 7.5, 6.5, 5.1],
            backgroundColor: function(context) {
                const value = context.raw;
                if (value >= 40) return colors.danger;
                if (value >= 20) return colors.accent;
                return colors.success;
            },
            borderRadius: 4
        }]
    },
    options: {
        ...commonOptions,
        scales: {
            y: {
                beginAtZero: true,
                max: 50,
                title: {
                    display: true,
                    text: 'Diesel Share (%)'
                }
            }
        },
        plugins: {
            ...commonOptions.plugins,
            title: {
                display: true,
                text: 'Diesel Share of New Car Sales (2005-2025)',
                font: { size: 16 }
            },
            annotation: {
                annotations: {
                    peak: {
                        type: 'label',
                        xValue: '2016',
                        yValue: 47,
                        content: 'Peak: 47%',
                        font: { size: 12 }
                    }
                }
            }
        }
    }
});

// ============================================================================
// 2. Fleet Age Distribution Chart
// ============================================================================
const fleetAgeCtx = document.getElementById('fleetAgeChart').getContext('2d');
new Chart(fleetAgeCtx, {
    type: 'bar',
    data: {
        labels: ['2022 (3yr)', '2021 (4yr)', '2020 (5yr)', '2019 (6yr)', '2018 (7yr)', '2017 (8yr)', '2016 (9yr)', '2015 (10yr)', '2014 (11yr)', '2013 (12yr)', '2012 (13yr)', '2011 (14yr)', '2010 (15yr)', '2009 (16yr)', '2008 (17yr)'],
        datasets: [{
            label: 'Active Diesel Vehicles (thousands)',
            data: [120, 200, 284, 568, 687, 950, 1134, 1109, 1044, 913, 784, 683, 587, 451, 389],
            backgroundColor: colors.primary,
            borderRadius: 4
        }]
    },
    options: {
        ...commonOptions,
        indexAxis: 'y',
        scales: {
            x: {
                title: {
                    display: true,
                    text: 'Vehicles (thousands)'
                }
            }
        },
        plugins: {
            ...commonOptions.plugins,
            title: {
                display: true,
                text: 'Active Diesel Fleet by Registration Year (tested 2024-2025)',
                font: { size: 16 }
            }
        }
    }
});

// ============================================================================
// 3. Survival Rate Chart
// ============================================================================
const survivalCtx = document.getElementById('survivalChart').getContext('2d');
new Chart(survivalCtx, {
    type: 'line',
    data: {
        labels: ['5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20'],
        datasets: [{
            label: 'Survival Rate (%)',
            data: [98.3, 97.1, 95.8, 94.4, 93.1, 91.2, 88.5, 85.1, 80.3, 73.1, 65.9, 56.9, 43.4, 34.5, 25.6, 18.4],
            borderColor: colors.accent,
            backgroundColor: 'rgba(237, 137, 54, 0.1)',
            fill: true,
            tension: 0.3,
            pointRadius: 5,
            pointBackgroundColor: colors.accent
        }]
    },
    options: {
        ...commonOptions,
        scales: {
            y: {
                beginAtZero: true,
                max: 100,
                title: {
                    display: true,
                    text: 'Vehicles Still on Road (%)'
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'Vehicle Age (years)'
                }
            }
        },
        plugins: {
            ...commonOptions.plugins,
            title: {
                display: true,
                text: 'Diesel Vehicle Survival Rate by Age',
                font: { size: 16 }
            }
        }
    }
});

// ============================================================================
// 4. Mileage Trend Chart
// ============================================================================
const mileageTrendCtx = document.getElementById('mileageTrendChart').getContext('2d');
new Chart(mileageTrendCtx, {
    type: 'line',
    data: {
        labels: ['2015', '2016', '2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024'],
        datasets: [
            {
                label: '5-year-old diesels',
                data: [60703, 61161, 59471, 57155, 56072, 54195, 50777, 50170, 49926, 50385],
                borderColor: colors.primary,
                backgroundColor: colors.primary,
                tension: 0.3,
                pointRadius: 4
            },
            {
                label: '10-year-old diesels',
                data: [109212, 108433, 107730, 106211, 102445, 101259, 99837, 97585, 95113, 93714],
                borderColor: colors.accent,
                backgroundColor: colors.accent,
                tension: 0.3,
                pointRadius: 4
            },
            {
                label: '15-year-old diesels',
                data: [137256, 136998, 137630, 134823, 132617, 132325, 130821, 130309, 128341, 125148],
                borderColor: colors.success,
                backgroundColor: colors.success,
                tension: 0.3,
                pointRadius: 4
            }
        ]
    },
    options: {
        ...commonOptions,
        scales: {
            y: {
                title: {
                    display: true,
                    text: 'Average Mileage at Test'
                },
                ticks: {
                    callback: function(value) {
                        return value.toLocaleString();
                    }
                }
            },
            x: {
                title: {
                    display: true,
                    text: 'Test Year'
                }
            }
        },
        plugins: {
            ...commonOptions.plugins,
            title: {
                display: true,
                text: 'Average Mileage at MOT by Vehicle Age Over Time',
                font: { size: 16 }
            }
        }
    }
});

// ============================================================================
// 5. Forecast Chart
// ============================================================================
const forecastCtx = document.getElementById('forecastChart').getContext('2d');
new Chart(forecastCtx, {
    type: 'line',
    data: {
        labels: ['2020', '2022', '2024', '2026', '2028', '2030', '2032', '2034', '2036', '2038', '2040'],
        datasets: [
            {
                label: 'Fleet Size (millions)',
                data: [10.6, 10.2, 9.7, 8.8, 7.7, 6.4, 4.9, 3.5, 2.4, 1.6, 1.1],
                borderColor: colors.primary,
                backgroundColor: 'rgba(26, 54, 93, 0.1)',
                fill: true,
                tension: 0.3,
                yAxisID: 'y'
            },
            {
                label: 'Consumption (billion litres)',
                data: [8.5, 7.8, 7.1, 6.2, 5.3, 4.2, 3.2, 2.2, 1.5, 1.0, 0.7],
                borderColor: colors.accent,
                backgroundColor: 'rgba(237, 137, 54, 0.1)',
                fill: true,
                tension: 0.3,
                yAxisID: 'y1'
            }
        ]
    },
    options: {
        ...commonOptions,
        scales: {
            y: {
                type: 'linear',
                display: true,
                position: 'left',
                title: {
                    display: true,
                    text: 'Fleet (millions)'
                },
                min: 0,
                max: 12
            },
            y1: {
                type: 'linear',
                display: true,
                position: 'right',
                title: {
                    display: true,
                    text: 'Consumption (B litres)'
                },
                min: 0,
                max: 10,
                grid: {
                    drawOnChartArea: false
                }
            }
        },
        plugins: {
            ...commonOptions.plugins,
            title: {
                display: true,
                text: 'Diesel Car Fleet and Consumption Forecast (2020-2040)',
                font: { size: 16 }
            }
        }
    }
});

console.log('Charts initialized');
