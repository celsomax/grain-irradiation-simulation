# Tutorial 1: Basic Grain Irradiation Simulation

This tutorial demonstrates the basic functionality of the Grain Irradiation Simulation Tool.

## Step 1: Basic Simulation

Let's start with a simple wheat irradiation simulation using a Cobalt-60 source.

```python
from grain_irradiation import IrradiationSimulator

# Create simulator instance
simulator = IrradiationSimulator()

# Create simulation parameters
params = simulator.create_simulation_parameters(
    source_type="Co-60",
    material_name="wheat",
    source_activity=1000,    # Ci
    source_distance=50,      # cm
    exposure_time=2.0,       # hours
    geometry_config={
        "shape": "sphere",
        "dimensions": {"radius": 1.0}  # cm
    }
)

# Run simulation
results = simulator.run_simulation(params, calculate_distribution=True)

# Display results
print(f"Mean dose: {results.mean_dose:.2f} Gy")
print(f"Dose uniformity: {results.dose_uniformity:.3f}")
print(f"Computation time: {results.computation_time:.2f} seconds")
```

## Step 2: Generate Visualization

```python
from grain_irradiation import DoseVisualizer

# Create visualizer
visualizer = DoseVisualizer(output_dir="./tutorial_plots")

# Generate 2D dose distribution plot
fig_2d = visualizer.plot_dose_distribution_2d(results, save_path="dose_map_2d.png")

# Generate 3D dose distribution plot
fig_3d = visualizer.plot_dose_distribution_3d(results, save_path="dose_map_3d.html")

# Generate dose histogram
fig_hist = visualizer.plot_dose_histogram(results, save_path="dose_histogram.png")

print("Plots saved in ./tutorial_plots/")
```

## Step 3: Parameter Optimization

Find the optimal exposure time for a target dose of 5 Gy:

```python
# Optimize exposure time
optimized_params = simulator.optimize_exposure_parameters(
    target_dose=5.0,         # Gy
    material_name="wheat",
    source_type="Co-60",
    source_activity=1000,
    source_distance=50,
    geometry_config={
        "shape": "sphere",
        "dimensions": {"radius": 1.0}
    }
)

print(f"Optimized exposure time: {optimized_params.exposure_time:.2f} hours")

# Verify optimization
optimized_results = simulator.run_simulation(optimized_params, calculate_distribution=False)
print(f"Achieved dose: {optimized_results.uniform_dose:.2f} Gy")
```

## Step 4: Generate Report

```python
# Generate detailed report
report = simulator.get_simulation_report(results)
print(report)

# Save report to file
with open("simulation_report.txt", "w") as f:
    f.write(report)
```

## Expected Output

When you run this tutorial, you should see output similar to:

```
Mean dose: 92.61 Gy
Dose uniformity: 0.925
Computation time: 0.08 seconds
Plots saved in ./tutorial_plots/
Optimized exposure time: 0.22 hours
Achieved dose: 5.00 Gy
```

## Next Steps

- Try different materials (rice, corn, water)
- Experiment with different source types (Cs-137, LinAc)
- Vary the geometry (cylinder, box shapes)
- Load and analyze experimental data (Tutorial 2)