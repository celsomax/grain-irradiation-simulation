#!/usr/bin/env python3
"""
Enhanced Grain Irradiation Simulation Example

This script demonstrates the use of GrainIrradiationSimulator class
as specified in the requirements, along with comprehensive functionality.
"""

import sys
from pathlib import Path

# Add src to path for local imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from grain_irradiation import GrainIrradiationSimulator, DoseVisualizer, DataLoader


def main():
    """Demonstrate comprehensive grain irradiation simulation capabilities."""
    print("=" * 70)
    print("ENHANCED GRAIN IRRADIATION SIMULATION - COMPREHENSIVE EXAMPLE")
    print("=" * 70)
    
    # Initialize the main simulator class as specified in requirements
    print("\n1. Initializing GrainIrradiationSimulator...")
    simulator = GrainIrradiationSimulator()
    
    print("   - Physics engine initialized")
    print("   - Grain quality models loaded")
    print("   - Data processing capabilities ready")
    
    # Demonstrate different grain types and treatments
    grains = ["wheat", "rice", "corn"]
    target_doses = [1.0, 2.5, 5.0]  # Gy
    
    print("\n2. Running simulations for different grains and doses...")
    
    results_summary = []
    
    for grain in grains:
        print(f"\n   Processing {grain.upper()}:")
        
        for dose in target_doses:
            # Find optimal parameters for target dose
            try:
                optimized_params = simulator.optimize_exposure_parameters(
                    target_dose=dose,
                    material_name=grain,
                    source_type="Co-60",
                    source_activity=1000,
                    source_distance=50,
                    geometry_config={
                        "shape": "sphere",
                        "dimensions": {"radius": 1.0}
                    }
                )
                
                # Run simulation
                results = simulator.run_simulation(optimized_params, calculate_distribution=False)
                
                # Calculate grain effects
                grain_effects = simulator.calculate_grain_effects(
                    dose=results.uniform_dose,
                    grain_type=grain,
                    temperature=25,
                    moisture_content=14
                )
                
                # Store results
                results_summary.append({
                    'grain': grain,
                    'target_dose': dose,
                    'actual_dose': results.uniform_dose,
                    'exposure_time': optimized_params.exposure_time,
                    'quality': grain_effects['quality_effects']['overall_quality'],
                    'germination': grain_effects['quality_effects']['germination_rate'],
                    'bacteria_reduction': grain_effects['microbial_inactivation']['bacteria']['log_reduction']
                })
                
                print(f"     {dose:.1f} Gy target: {results.uniform_dose:.2f} Gy achieved, "
                      f"Quality: {grain_effects['quality_effects']['overall_quality']:.1f}%")
                
            except Exception as e:
                print(f"     Error with {dose:.1f} Gy: {e}")
    
    # Display comprehensive results table
    print("\n3. SIMULATION RESULTS SUMMARY")
    print("=" * 70)
    print(f"{'Grain':<8} {'Target':<8} {'Actual':<8} {'Time':<8} {'Quality':<8} {'Germ.':<8} {'Log Red.':<8}")
    print(f"{'Type':<8} {'(Gy)':<8} {'(Gy)':<8} {'(h)':<8} {'(%)':<8} {'(%)':<8} {'(cycles)':<8}")
    print("-" * 70)
    
    for result in results_summary:
        print(f"{result['grain']:<8} "
              f"{result['target_dose']:<8.1f} "
              f"{result['actual_dose']:<8.2f} "
              f"{result['exposure_time']:<8.3f} "
              f"{result['quality']:<8.1f} "
              f"{result['germination']:<8.1f} "
              f"{result['bacteria_reduction']:<8.1f}")
    
    # Demonstrate data loading and analysis
    print("\n4. Loading and analyzing experimental data...")
    data_loader = DataLoader()
    
    try:
        experimental_data = data_loader.load_data("examples/data/experimental_data.csv")
        
        # Validate data
        validation = data_loader.validate_data(experimental_data)
        print(f"   - Loaded {len(experimental_data)} experimental records")
        print(f"   - Validation: {validation.valid_records}/{validation.total_records} valid")
        
        # Filter for wheat data
        wheat_data = data_loader.filter_data(experimental_data, material='wheat')
        print(f"   - Found {len(wheat_data)} wheat experiments")
        
        # Get summary statistics
        summary = data_loader.get_summary_statistics(wheat_data)
        print(f"   - Dose range: {summary['dose_statistics']['min']:.1f} - {summary['dose_statistics']['max']:.1f} Gy")
        print(f"   - Mean dose: {summary['dose_statistics']['mean']:.1f} ± {summary['dose_statistics']['std']:.1f} Gy")
        
    except Exception as e:
        print(f"   Warning: Could not load experimental data - {e}")
    
    # Demonstrate treatment recommendations
    print("\n5. Treatment recommendations for different applications...")
    
    applications = [
        ("food", 3.0, "Food grade wheat"),
        ("seed", 2.0, "Seed wheat (preserve germination)"),
        ("feed", 4.0, "Feed grade corn")
    ]
    
    for use, log_reduction, description in applications:
        grain_type = "corn" if "corn" in description else "wheat"
        recommendation = simulator.get_treatment_recommendation(
            grain_type=grain_type,
            target_log_reduction=log_reduction,
            target_use=use
        )
        
        print(f"\n   {description}:")
        print(f"     - Required dose: {recommendation['required_dose_Gy']:.2f} Gy")
        print(f"     - Safety level: {recommendation['safety_level']}")
        print(f"     - Regulatory status: {recommendation['validation']['regulatory_status']}")
        
        if recommendation['validation']['warnings']:
            print(f"     - Warnings: {len(recommendation['validation']['warnings'])}")
    
    # Demonstrate comparison with experimental data (if available)
    print("\n6. Model validation against experimental data...")
    
    try:
        # Use a subset of experimental data for comparison
        if 'experimental_data' in locals() and len(experimental_data) > 0:
            comparison = simulator.compare_with_experimental(experimental_data[:5])
            
            print(f"   - Compared {len(comparison.experimental_data)} experiments")
            print(f"   - Correlation coefficient: {comparison.correlation_coefficient:.3f}")
            print(f"   - Mean absolute error: {comparison.mean_absolute_error:.2f} Gy")
            print(f"   - Relative error: {comparison.relative_error:.1f}%")
        else:
            print("   - No experimental data available for comparison")
            
    except Exception as e:
        print(f"   - Comparison failed: {e}")
    
    # Generate comprehensive visualization
    print("\n7. Generating comprehensive dose distribution analysis...")
    
    # Create a detailed simulation for visualization
    detailed_params = simulator.create_simulation_parameters(
        source_type="Co-60",
        material_name="wheat",
        source_activity=1000,
        source_distance=50,
        exposure_time=0.65,  # Optimized for ~1 Gy
        geometry_config={
            "shape": "sphere",
            "dimensions": {"radius": 2.0}  # Larger sample for better visualization
        }
    )
    
    detailed_results = simulator.run_simulation(detailed_params, calculate_distribution=True)
    
    print(f"   - Generated dose distribution: {detailed_results.mean_dose:.2f} Gy mean")
    print(f"   - Dose uniformity: {detailed_results.dose_uniformity:.3f}")
    print(f"   - Computation time: {detailed_results.computation_time:.3f} seconds")
    
    # Save visualization plots
    try:
        visualizer = DoseVisualizer(output_dir="./enhanced_plots")
        plot_files = visualizer.save_all_plots(detailed_results, prefix="enhanced_example")
        
        print(f"\n   VISUALIZATION FILES CREATED:")
        for plot_type, filepath in plot_files.items():
            print(f"     {plot_type}: {filepath}")
            
    except Exception as e:
        print(f"   Warning: Visualization failed - {e}")
    
    # Display final statistics
    print("\n8. Simulation session summary...")
    history_summary = simulator.get_history_summary()
    print(f"   - Total simulations run: {history_summary['total_simulations']}")
    if history_summary['total_simulations'] > 0:
        print(f"   - Dose range: {history_summary['mean_dose_range'][0]:.1f} - {history_summary['mean_dose_range'][1]:.1f} Gy")
        print(f"   - Average computation time: {history_summary['mean_computation_time']:.3f} seconds")
    
    print(f"\n" + "=" * 70)
    print("ENHANCED SIMULATION COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print("\nCapabilities demonstrated:")
    print("✓ GrainIrradiationSimulator main class (as specified in requirements)")
    print("✓ Multiple grain types and dose levels")
    print("✓ Parameter optimization for target doses")
    print("✓ Grain quality and microbial inactivation models")
    print("✓ Treatment recommendations for different applications")
    print("✓ Experimental data loading and validation")
    print("✓ Model validation against experimental data")
    print("✓ Comprehensive dose distribution visualization")
    print("✓ Regulatory compliance checking")
    print("\nNext steps:")
    print("- Explore CLI commands: grain-sim --help")
    print("- Check visualization files in ./enhanced_plots/")
    print("- Review tutorials in examples/tutorials/")
    print("- Load your own experimental data")


if __name__ == "__main__":
    main()