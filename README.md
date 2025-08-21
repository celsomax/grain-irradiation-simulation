# Grain Irradiation Simulation Tool

A comprehensive Python software for simulating grain and seed irradiation processes using experimental data. This tool is designed for educational and research purposes in food science and radiation processing.

## Features

### Core Functionality
- **Physics-based simulations**: Validated physical models for radiation dose calculations
- **Multiple radiation sources**: Support for Cobalt-60, Cesium-137, and Linear Accelerators
- **Various sample geometries**: Spherical, cylindrical, and box-shaped samples
- **Spatial dose distribution**: 2D and 3D dose mapping within samples
- **Experimental data integration**: Load, validate, and compare with experimental results

### User Interfaces
- **Command Line Interface (CLI)**: Powerful scripting and automation capabilities
- **Graphical User Interface (GUI)**: User-friendly Tkinter-based interface
- **Configuration system**: YAML/JSON configuration files for reproducible workflows

### Visualization and Analysis
- **2D/3D plotting**: Interactive dose distribution visualizations
- **Statistical analysis**: Comprehensive data validation and summary statistics
- **Experimental comparison**: Correlation analysis between simulated and measured data
- **Export capabilities**: Save results in multiple formats (JSON, CSV, images)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Install from source
```bash
git clone https://github.com/celsomax/grain-irradiation-simulation.git
cd grain-irradiation-simulation
pip install -e .
```

### Install dependencies only
```bash
pip install -r requirements.txt
```

## Quick Start

### Command Line Interface

1. **Run a basic simulation**:
```bash
grain-sim simulate --source Co-60 --material wheat --activity 1000 --distance 50 --time 2
```

2. **Load and validate experimental data**:
```bash
grain-sim load-data examples/data/experimental_data.csv --validate --summary
```

3. **Compare experimental data with simulations**:
```bash
grain-sim compare examples/data/experimental_data.csv --simulate --plot
```

4. **Optimize exposure parameters**:
```bash
grain-sim optimize --target-dose 5.0 --material wheat --source Co-60 --activity 1000
```

### Graphical User Interface

Launch the GUI application:
```bash
python -m grain_irradiation.gui.app
```

### Python API

```python
from grain_irradiation import IrradiationSimulator

# Create simulator
simulator = IrradiationSimulator()

# Set up simulation parameters
params = simulator.create_simulation_parameters(
    source_type="Co-60",
    material_name="wheat",
    source_activity=1000,
    source_distance=50,
    exposure_time=2.0,
    geometry_config={
        "shape": "sphere",
        "dimensions": {"radius": 1.0}
    }
)

# Run simulation
results = simulator.run_simulation(params)

# Display results
print(f"Mean dose: {results.mean_dose:.2f} Gy")
print(f"Dose uniformity: {results.dose_uniformity:.3f}")
```

## Documentation

### Scientific Background

The simulation is based on validated physical models from radiation processing literature:

- **Dose rate calculations**: Inverse square law for point sources
- **Attenuation modeling**: Beer-Lambert law for material penetration
- **Spatial distribution**: Monte Carlo-inspired dose mapping
- **Source modeling**: Cobalt-60, Cesium-137, and electron beam characteristics

### Supported Materials

Pre-configured materials with validated properties:
- **Wheat**: ρ = 0.8 g/cm³, Z_eff = 6.5
- **Rice**: ρ = 0.75 g/cm³, Z_eff = 6.3  
- **Corn**: ρ = 0.85 g/cm³, Z_eff = 6.7
- **Water**: ρ = 1.0 g/cm³, Z_eff = 7.4

### Radiation Sources

- **Cobalt-60**: γ-rays, E = 1.25 MeV (average), t₁/₂ = 5.27 years
- **Cesium-137**: γ-rays, E = 0.662 MeV, t₁/₂ = 30.1 years
- **Linear Accelerator**: Electrons, E = 10 MeV (configurable)

## Examples

### Example 1: Basic Wheat Irradiation
```python
# Simulate wheat irradiation with Co-60
params = simulator.create_simulation_parameters(
    source_type="Co-60",
    material_name="wheat",
    source_activity=1000,  # Ci
    source_distance=50,    # cm
    exposure_time=2.0,     # hours
    geometry_config={"shape": "sphere", "dimensions": {"radius": 1.0}}
)

results = simulator.run_simulation(params, calculate_distribution=True)

# Generate visualization
from grain_irradiation import DoseVisualizer
visualizer = DoseVisualizer()
visualizer.plot_dose_distribution_2d(results, save_path="dose_map.png")
```

### Example 2: Load Experimental Data
```python
from grain_irradiation import DataLoader

loader = DataLoader()
data = loader.load_data("experimental_data.csv")

# Validate data quality
validation = loader.validate_data(data)
print(f"Valid records: {validation.valid_records}/{validation.total_records}")

# Generate summary statistics
summary = loader.get_summary_statistics(data)
print(f"Mean dose: {summary['dose_statistics']['mean']:.2f} Gy")
```

### Example 3: Parameter Optimization
```python
# Find optimal exposure time for target dose
optimized_params = simulator.optimize_exposure_parameters(
    target_dose=5.0,       # Gy
    material_name="rice",
    source_type="Co-60",
    source_activity=800,   # Ci
    source_distance=60     # cm
)

print(f"Optimized exposure time: {optimized_params.exposure_time:.2f} hours")
```

## Configuration

Create a configuration file (`config.yaml`):

```yaml
simulation:
  default_source: "Co-60"
  default_material: "wheat"
  grid_resolution: 50

visualization:
  output_directory: "./plots"
  dpi: 300
  colormap: "plasma"

logging:
  level: "INFO"
  file: "simulation.log"
```

Load configuration:
```bash
grain-sim config --load config.yaml
```

## Data Formats

### Experimental Data (CSV)
```csv
sample_id,material,dose,dose_rate,exposure_time,source_type,source_activity,distance,temperature,humidity
WH001,wheat,2.5,1.25,2.0,Co-60,1000,50,25,65
```

### Experimental Data (JSON)
```json
{
  "experiments": [
    {
      "sample_id": "WH001",
      "material": "wheat",
      "dose": 2.5,
      "dose_rate": 1.25,
      "exposure_time": 2.0,
      "source_type": "Co-60",
      "source_activity": 1000,
      "distance": 50,
      "temperature": 25,
      "humidity": 65
    }
  ]
}
```

## Testing

Run the test suite:
```bash
python -m pytest tests/ -v
```

Run specific test modules:
```bash
python -m pytest tests/test_simulation.py -v
```

Generate coverage report:
```bash
python -m pytest tests/ --cov=src/grain_irradiation --cov-report=html
```

## Development

### Project Structure
```
grain-irradiation-simulation/
├── src/grain_irradiation/          # Main package
│   ├── core/                       # Core physics and simulation
│   ├── data/                       # Data loading and validation
│   ├── visualization/              # Plotting and visualization
│   ├── cli/                        # Command line interface
│   └── gui/                        # Graphical user interface
├── tests/                          # Unit and integration tests
├── examples/                       # Example data and tutorials
├── config/                         # Configuration files
├── docs/                           # Documentation
└── requirements.txt                # Dependencies
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Make changes and add tests
4. Run tests (`python -m pytest`)
5. Commit changes (`git commit -am 'Add new feature'`)
6. Push to branch (`git push origin feature/new-feature`)
7. Create Pull Request

### Code Style

- Follow PEP 8 style guidelines
- Use type hints where applicable
- Write comprehensive docstrings
- Maintain test coverage above 80%

## Scientific References

1. Cleland, M. R., & Parks, L. A. (2003). Medium and high-energy electron beam sterilization. *Radiation Physics and Chemistry*, 68(6), 975-983.

2. IAEA. (2015). *Manual of Good Practice in Food Irradiation*. Technical Document Series No. 481. International Atomic Energy Agency.

3. Turner, J. E. (2007). *Atoms, Radiation, and Radiation Protection*. 3rd Edition. Wiley-VCH.

4. Kume, T., et al. (2009). Status of food irradiation in the world. *Radiation Physics and Chemistry*, 78(3), 222-226.

## License

MIT License - see LICENSE file for details.

## Support

- **Documentation**: [GitHub Wiki](https://github.com/celsomax/grain-irradiation-simulation/wiki)
- **Issues**: [GitHub Issues](https://github.com/celsomax/grain-irradiation-simulation/issues)
- **Discussions**: [GitHub Discussions](https://github.com/celsomax/grain-irradiation-simulation/discussions)

## Acknowledgments

This software was developed for educational and research purposes in food irradiation science. We acknowledge the contributions of the radiation processing community and the open-source Python ecosystem that made this project possible.
