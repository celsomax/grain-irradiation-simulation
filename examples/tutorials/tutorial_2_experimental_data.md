# Tutorial 2: Working with Experimental Data

This tutorial shows how to load, validate, and analyze experimental irradiation data.

## Step 1: Load Experimental Data

```python
from grain_irradiation import DataLoader

# Create data loader instance
loader = DataLoader()

# Load data from CSV file
data = loader.load_data("examples/data/experimental_data.csv")
print(f"Loaded {len(data)} experimental records")

# Display first few records
for i, experiment in enumerate(data[:3]):
    print(f"\nRecord {i+1}:")
    print(f"  Sample ID: {experiment.sample_id}")
    print(f"  Material: {experiment.material}")
    print(f"  Dose: {experiment.dose:.2f} Gy")
    print(f"  Source: {experiment.source_type}")
```

## Step 2: Data Validation

```python
# Validate data quality
validation_result = loader.validate_data(data)

print(f"\nValidation Results:")
print(f"  Total records: {validation_result.total_records}")
print(f"  Valid records: {validation_result.valid_records}")
print(f"  Validation rate: {validation_result.validation_rate:.1f}%")

# Show errors and warnings
if validation_result.errors:
    print(f"\nErrors found:")
    for error in validation_result.errors[:5]:  # Show first 5
        print(f"  - {error}")

if validation_result.warnings:
    print(f"\nWarnings found:")
    for warning in validation_result.warnings[:5]:  # Show first 5
        print(f"  - {warning}")
```

## Step 3: Data Analysis

```python
# Generate summary statistics
summary = loader.get_summary_statistics(data)

print(f"\nData Summary:")
print(f"  Total records: {summary['total_records']}")
print(f"  Dose statistics:")
print(f"    Mean: {summary['dose_statistics']['mean']:.2f} ± {summary['dose_statistics']['std']:.2f} Gy")
print(f"    Range: {summary['dose_statistics']['min']:.2f} - {summary['dose_statistics']['max']:.2f} Gy")
print(f"    Median: {summary['dose_statistics']['median']:.2f} Gy")

print(f"  Materials: {list(summary['material_distribution'].keys())}")
print(f"  Source types: {list(summary['source_type_distribution'].keys())}")
```

## Step 4: Data Filtering

```python
# Filter data by material
wheat_data = loader.filter_data(data, material="wheat")
print(f"Wheat experiments: {len(wheat_data)}")

# Filter data by dose range
low_dose_data = loader.filter_data(data, dose_max=3.0)
print(f"Low dose experiments (≤3 Gy): {len(low_dose_data)}")

# Filter by multiple criteria
co60_wheat_data = loader.filter_data(data, material="wheat", source_type="Co-60")
print(f"Co-60 wheat experiments: {len(co60_wheat_data)}")
```

## Step 5: Data Visualization

```python
from grain_irradiation import DoseVisualizer

# Create visualizer
visualizer = DoseVisualizer(output_dir="./tutorial_plots")

# Generate data overview plots
fig = visualizer.plot_experimental_data_overview(data, save_path="data_overview.png")
print("Data overview plot saved")
```

## Step 6: Compare with Simulations

```python
from grain_irradiation import IrradiationSimulator

# Create simulator
simulator = IrradiationSimulator()

# Run comparison with experimental data
comparison = simulator.compare_with_experimental(data)

print(f"\nExperimental vs Simulation Comparison:")
print(f"  Correlation coefficient: {comparison.correlation_coefficient:.3f}")
print(f"  Mean absolute error: {comparison.mean_absolute_error:.2f} Gy")
print(f"  Relative error: {comparison.relative_error:.1f}%")
print(f"  Number of comparisons: {comparison.statistics['n_comparisons']}")

# Generate comparison plot
fig_comp = visualizer.plot_experimental_comparison(comparison, save_path="exp_vs_sim.png")
print("Comparison plot saved")
```

## Step 7: Export Processed Data

```python
# Save filtered data
loader.save_data(wheat_data, "wheat_experiments.csv", format="csv")
loader.save_data(wheat_data, "wheat_experiments.json", format="json")

print("Filtered data exported")
```

## Expected Output

```
Loaded 15 experimental records

Record 1:
  Sample ID: WH001
  Material: wheat
  Dose: 2.50 Gy
  Source: Co-60

Validation Results:
  Total records: 15
  Valid records: 15
  Validation rate: 100.0%

Data Summary:
  Total records: 15
  Dose statistics:
    Mean: 4.10 ± 2.68 Gy
    Range: 0.50 - 10.00 Gy
    Median: 3.00 Gy
  Materials: ['wheat', 'rice', 'corn']
  Source types: ['Co-60', 'Cs-137', 'LinAc']

Wheat experiments: 6
Low dose experiments (≤3 Gy): 8
Co-60 wheat experiments: 5

Experimental vs Simulation Comparison:
  Correlation coefficient: 0.892
  Mean absolute error: 12.45 Gy
  Relative error: 23.1%
  Number of comparisons: 15
```

## Creating Your Own Data

You can create your own experimental data files in CSV format:

```csv
sample_id,material,dose,dose_rate,exposure_time,source_type,source_activity,distance,temperature,humidity,notes
MY001,wheat,3.5,1.75,2.0,Co-60,1000,45,25,65,My experiment
MY002,rice,2.0,1.0,2.0,Co-60,800,60,20,70,Control sample
```

Or in JSON format:

```json
[
  {
    "sample_id": "MY001",
    "material": "wheat",
    "dose": 3.5,
    "dose_rate": 1.75,
    "exposure_time": 2.0,
    "source_type": "Co-60",
    "source_activity": 1000,
    "distance": 45,
    "temperature": 25,
    "humidity": 65,
    "notes": "My experiment"
  }
]
```

## Next Steps

- Try loading your own experimental data
- Experiment with different filtering criteria
- Analyze dose uniformity across different materials
- Use the validation results to improve data quality