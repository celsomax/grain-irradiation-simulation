#!/usr/bin/env python3
"""
Basic Grain Irradiation Simulation Example

This script demonstrates the core functionality of the grain irradiation
simulation tool with a complete workflow from simulation to analysis.
"""

import sys
from pathlib import Path

# Add src to path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from grain_irradiation import IrradiationSimulator, DoseVisualizer
from grain_irradiation.core.models import MicrobialType


def main():
    """Run basic grain irradiation simulation example."""
    print("=" * 60)
    print("GRAIN IRRADIATION SIMULATION - BASIC EXAMPLE")
    print("=" * 60)
    
    # Initialize simulator
    print("\n1. Initializing simulation engine...")
    simulator = IrradiationSimulator()
    
    # Create simulation parameters for wheat irradiation
    print("\n2. Setting up simulation parameters...")
    print("   - Material: Wheat")
    print("   - Source: Co-60")
    print("   - Activity: 1000 Ci")
    print("   - Distance: 50 cm")
    print("   - Exposure time: 2.0 hours")
    print("   - Geometry: Sphere (radius 1.0 cm)")
    
    params = simulator.create_simulation_parameters(
        source_type="Co-60",
        material_name="wheat",
        source_activity=1000,    # Ci
        source_distance=50,      # cm
        exposure_time=2.0,       # hours
        geometry_config={
            "shape": "sphere",
            "dimensions": {"radius": 1.0}  # cm
        },
        temperature=25,          # °C
        humidity=65             # %
    )
    
    # Run basic dose calculation
    print("\n3. Running dose calculation simulation...")
    results = simulator.run_simulation(params, calculate_distribution=False)
    
    print(f"\nSIMULATION RESULTS:")
    print(f"  Uniform dose: {results.uniform_dose:.2f} Gy")
    print(f"  Computation time: {results.computation_time:.3f} seconds")
    
    # Calculate grain effects
    print("\n4. Analyzing grain irradiation effects...")
    grain_effects = simulator.calculate_grain_effects(
        dose=results.uniform_dose,
        grain_type="wheat",
        temperature=25,
        moisture_content=14
    )
    
    print(f"\nMICROBIAL INACTIVATION:")
    bacteria = grain_effects['microbial_inactivation']['bacteria']
    print(f"  Bacteria: {bacteria['log_reduction']:.2f} log reduction")
    print(f"  Survival fraction: {bacteria['survival_fraction']:.2e}")
    
    mold = grain_effects['microbial_inactivation']['mold']
    print(f"  Mold: {mold['log_reduction']:.2f} log reduction")
    print(f"  Survival fraction: {mold['survival_fraction']:.2e}")
    
    print(f"\nQUALITY EFFECTS:")
    quality = grain_effects['quality_effects']
    print(f"  Germination rate: {quality['germination_rate']:.1f}%")
    print(f"  Protein retention: {quality['protein_retention']:.1f}%")
    print(f"  Vitamin retention: {quality['vitamin_retention']:.1f}%")
    print(f"  Overall quality: {quality['overall_quality']:.1f}%")
    print(f"  Sensory score: {quality['sensory_score']:.1f}/10")
    
    # Treatment validation
    validation = grain_effects['treatment_validation']
    print(f"\nTREATMENT VALIDATION:")
    print(f"  Status: {validation['regulatory_status']}")
    print(f"  Valid: {'Yes' if validation['is_valid'] else 'No'}")
    if validation['warnings']:
        print(f"  Warnings: {len(validation['warnings'])}")
        for warning in validation['warnings']:
            print(f"    - {warning}")
    
    # Get treatment recommendation
    print("\n5. Getting treatment recommendation...")
    recommendation = simulator.get_treatment_recommendation(
        grain_type="wheat",
        target_log_reduction=3.0,
        target_use="food"
    )
    
    print(f"\nTREATMENT RECOMMENDATION:")
    print(f"  Target: {recommendation['target_log_reduction']} log reduction")
    print(f"  Required dose: {recommendation['required_dose_Gy']:.2f} Gy")
    print(f"  Safety level: {recommendation['safety_level']}")
    print(f"  Recommendation: {recommendation['recommendation']}")
    
    # Run dose distribution simulation
    print("\n6. Running dose distribution simulation...")
    results_3d = simulator.run_simulation(params, calculate_distribution=True)
    
    print(f"\nDOSE DISTRIBUTION RESULTS:")
    print(f"  Mean dose: {results_3d.mean_dose:.2f} Gy")
    print(f"  Max dose: {results_3d.max_dose:.2f} Gy")
    print(f"  Min dose: {results_3d.min_dose:.2f} Gy")
    print(f"  Dose uniformity: {results_3d.dose_uniformity:.3f}")
    print(f"  Computation time: {results_3d.computation_time:.3f} seconds")
    
    # Generate visualizations
    print("\n7. Generating visualization plots...")
    visualizer = DoseVisualizer(output_dir="./example_plots")
    
    try:
        # Save all plots
        plot_files = visualizer.save_all_plots(results_3d, prefix="basic_example")
        print(f"\nVISUALIZATION FILES CREATED:")
        for plot_type, filepath in plot_files.items():
            print(f"  {plot_type}: {filepath}")
    except Exception as e:
        print(f"  Warning: Could not generate plots - {e}")
    
    # Parameter optimization example
    print("\n8. Demonstrating parameter optimization...")
    try:
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
        
        print(f"\nOPTIMIZATION RESULTS:")
        print(f"  Target dose: 5.0 Gy")
        print(f"  Optimized exposure time: {optimized_params.exposure_time:.2f} hours")
        
        # Verify optimization
        verification_results = simulator.run_simulation(optimized_params, False)
        print(f"  Achieved dose: {verification_results.uniform_dose:.2f} Gy")
        print(f"  Error: {abs(verification_results.uniform_dose - 5.0):.3f} Gy")
        
    except Exception as e:
        print(f"  Warning: Optimization failed - {e}")
    
    print(f"\n" + "=" * 60)
    print("SIMULATION COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Check generated plots in ./example_plots/")
    print("2. Try the CLI: grain-sim simulate --help")
    print("3. Explore the GUI: python -m grain_irradiation.gui.app")
    print("4. See tutorials in examples/tutorials/")


if __name__ == "__main__":
    main()