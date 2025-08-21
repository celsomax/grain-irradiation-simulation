"""
Command Line Interface for grain irradiation simulation.

This module provides a user-friendly CLI for running simulations,
analyzing data, and generating reports.
"""

import argparse
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

from ..core.simulator import IrradiationSimulator, SimulationParameters
from ..core.physics import RadiationSource, MaterialProperties, GeometryConfig
from ..data.loader import DataLoader
from ..visualization.plotter import DoseVisualizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CLI:
    """Command Line Interface for grain irradiation simulation."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.simulator = IrradiationSimulator()
        self.data_loader = DataLoader()
        self.visualizer = DoseVisualizer()
        
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description='Grain Irradiation Simulation Tool',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s simulate --source Co-60 --material wheat --activity 1000 --distance 50 --time 2
  %(prog)s load-data experiments.csv --validate
  %(prog)s compare experiments.csv --simulate
  %(prog)s optimize --target-dose 5.0 --material rice --source Co-60 --activity 500
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Simulate command
        sim_parser = subparsers.add_parser('simulate', help='Run irradiation simulation')
        sim_parser.add_argument('--source', required=True, 
                               choices=['Co-60', 'Cs-137', 'LinAc'],
                               help='Radiation source type')
        sim_parser.add_argument('--material', required=True,
                               choices=['wheat', 'rice', 'corn', 'water'],
                               help='Material to be irradiated')
        sim_parser.add_argument('--activity', type=float, required=True,
                               help='Source activity (Ci for isotopes, kW for LinAc)')
        sim_parser.add_argument('--distance', type=float, required=True,
                               help='Distance from source (cm)')
        sim_parser.add_argument('--time', type=float, required=True,
                               help='Exposure time (hours)')
        sim_parser.add_argument('--geometry', default='sphere',
                               choices=['sphere', 'cylinder', 'box'],
                               help='Sample geometry')
        sim_parser.add_argument('--geometry-size', type=float, default=1.0,
                               help='Characteristic size (radius for sphere, etc.)')
        sim_parser.add_argument('--temperature', type=float,
                               help='Temperature (°C)')
        sim_parser.add_argument('--humidity', type=float,
                               help='Humidity (%)')
        sim_parser.add_argument('--output', '-o',
                               help='Output file for results (JSON)')
        sim_parser.add_argument('--plot', action='store_true',
                               help='Generate visualization plots')
        sim_parser.add_argument('--no-distribution', action='store_true',
                               help='Skip dose distribution calculation')
        
        # Load data command
        load_parser = subparsers.add_parser('load-data', help='Load and validate experimental data')
        load_parser.add_argument('file', help='Input data file')
        load_parser.add_argument('--validate', action='store_true',
                                help='Validate data')
        load_parser.add_argument('--summary', action='store_true',
                                help='Show data summary')
        load_parser.add_argument('--plot', action='store_true',
                                help='Generate data overview plots')
        load_parser.add_argument('--output', '-o',
                                help='Output file for processed data')
        
        # Compare command
        compare_parser = subparsers.add_parser('compare', 
                                             help='Compare experimental data with simulations')
        compare_parser.add_argument('file', help='Experimental data file')
        compare_parser.add_argument('--simulate', action='store_true',
                                   help='Run simulations for comparison')
        compare_parser.add_argument('--plot', action='store_true',
                                   help='Generate comparison plots')
        compare_parser.add_argument('--output', '-o',
                                   help='Output file for comparison results')
        
        # Optimize command
        opt_parser = subparsers.add_parser('optimize', help='Optimize irradiation parameters')
        opt_parser.add_argument('--target-dose', type=float, required=True,
                               help='Target dose (Gy)')
        opt_parser.add_argument('--material', required=True,
                               choices=['wheat', 'rice', 'corn', 'water'],
                               help='Material to be irradiated')
        opt_parser.add_argument('--source', required=True,
                               choices=['Co-60', 'Cs-137', 'LinAc'],
                               help='Radiation source type')
        opt_parser.add_argument('--activity', type=float, required=True,
                               help='Source activity')
        opt_parser.add_argument('--distance', type=float, default=50.0,
                               help='Distance from source (cm)')
        opt_parser.add_argument('--geometry', default='sphere',
                               choices=['sphere', 'cylinder', 'box'],
                               help='Sample geometry')
        opt_parser.add_argument('--geometry-size', type=float, default=1.0,
                               help='Characteristic size')
        opt_parser.add_argument('--tolerance', type=float, default=0.05,
                               help='Optimization tolerance')
        opt_parser.add_argument('--output', '-o',
                               help='Output file for optimized parameters')
        
        # Config command
        config_parser = subparsers.add_parser('config', help='Configuration management')
        config_parser.add_argument('--create-template', 
                                  help='Create configuration template file')
        config_parser.add_argument('--load',
                                  help='Load configuration from file')
        config_parser.add_argument('--validate',
                                  help='Validate configuration file')
        
        # General options
        parser.add_argument('--verbose', '-v', action='store_true',
                           help='Verbose output')
        parser.add_argument('--quiet', '-q', action='store_true',
                           help='Quiet output')
        parser.add_argument('--log-file',
                           help='Log file path')
        
        return parser
    
    def setup_logging(self, args):
        """Setup logging based on arguments."""
        if args.quiet:
            level = logging.WARNING
        elif args.verbose:
            level = logging.DEBUG
        else:
            level = logging.INFO
        
        logging.getLogger().setLevel(level)
        
        if args.log_file:
            file_handler = logging.FileHandler(args.log_file)
            file_handler.setLevel(level)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            logging.getLogger().addHandler(file_handler)
    
    def run_simulate(self, args) -> int:
        """Run simulation command."""
        try:
            # Create geometry configuration
            if args.geometry == 'sphere':
                geometry_config = {
                    'shape': 'sphere',
                    'dimensions': {'radius': args.geometry_size}
                }
            elif args.geometry == 'cylinder':
                geometry_config = {
                    'shape': 'cylinder',
                    'dimensions': {'radius': args.geometry_size, 'height': args.geometry_size * 2}
                }
            else:  # box
                geometry_config = {
                    'shape': 'box',
                    'dimensions': {
                        'length': args.geometry_size,
                        'width': args.geometry_size,
                        'height': args.geometry_size
                    }
                }
            
            # Create simulation parameters
            params = self.simulator.create_simulation_parameters(
                source_type=args.source,
                material_name=args.material,
                source_activity=args.activity,
                source_distance=args.distance,
                exposure_time=args.time,
                geometry_config=geometry_config,
                temperature=args.temperature,
                humidity=args.humidity
            )
            
            # Run simulation
            calculate_distribution = not args.no_distribution
            results = self.simulator.run_simulation(params, calculate_distribution)
            
            # Print results
            print("\\n" + "="*60)
            print("SIMULATION RESULTS")
            print("="*60)
            print(f"Uniform dose: {results.uniform_dose:.2f} Gy")
            print(f"Mean dose: {results.mean_dose:.2f} Gy")
            print(f"Max dose: {results.max_dose:.2f} Gy")
            print(f"Min dose: {results.min_dose:.2f} Gy")
            print(f"Dose uniformity: {results.dose_uniformity:.3f}")
            print(f"Computation time: {results.computation_time:.2f} s")
            
            # Save results if requested
            if args.output:
                output_data = {
                    'parameters': {
                        'source': results.parameters.source.value,
                        'material': results.parameters.material.name,
                        'activity': results.parameters.source_activity,
                        'distance': results.parameters.source_distance,
                        'exposure_time': results.parameters.exposure_time,
                        'geometry': {
                            'shape': results.parameters.geometry.shape,
                            'dimensions': results.parameters.geometry.dimensions
                        }
                    },
                    'results': results.get_summary()
                }
                
                with open(args.output, 'w') as f:
                    json.dump(output_data, f, indent=2)
                print(f"\\nResults saved to {args.output}")
            
            # Generate plots if requested
            if args.plot and calculate_distribution:
                plot_files = self.visualizer.save_all_plots(results, "cli_simulation")
                print(f"\\nPlots saved:")
                for plot_type, filepath in plot_files.items():
                    print(f"  {plot_type}: {filepath}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            return 1
    
    def run_load_data(self, args) -> int:
        """Run load data command."""
        try:
            # Load data
            data = self.data_loader.load_data(args.file)
            print(f"Loaded {len(data)} experimental records from {args.file}")
            
            # Validate if requested
            if args.validate:
                validation = self.data_loader.validate_data(data)
                print(f"\\nValidation Results:")
                print(f"  Valid records: {validation.valid_records}/{validation.total_records} "
                      f"({validation.validation_rate:.1f}%)")
                
                if validation.errors:
                    print(f"  Errors: {len(validation.errors)}")
                    for error in validation.errors[:5]:  # Show first 5 errors
                        print(f"    - {error}")
                
                if validation.warnings:
                    print(f"  Warnings: {len(validation.warnings)}")
                    for warning in validation.warnings[:5]:  # Show first 5 warnings
                        print(f"    - {warning}")
            
            # Show summary if requested
            if args.summary:
                summary = self.data_loader.get_summary_statistics(data)
                print(f"\\nData Summary:")
                print(f"  Total records: {summary['total_records']}")
                print(f"  Dose range: {summary['dose_statistics']['min']:.2f} - "
                      f"{summary['dose_statistics']['max']:.2f} Gy")
                print(f"  Mean dose: {summary['dose_statistics']['mean']:.2f} ± "
                      f"{summary['dose_statistics']['std']:.2f} Gy")
                print(f"  Materials: {', '.join(summary['material_distribution'].keys())}")
                print(f"  Sources: {', '.join(summary['source_type_distribution'].keys())}")
            
            # Generate plots if requested
            if args.plot:
                plot_path = "experimental_data_overview.png"
                self.visualizer.plot_experimental_data_overview(data, plot_path)
                print(f"\\nData overview plot saved to {plot_path}")
            
            # Save processed data if requested
            if args.output:
                self.data_loader.save_data(data, args.output)
                print(f"\\nProcessed data saved to {args.output}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Data loading error: {e}")
            return 1
    
    def run_compare(self, args) -> int:
        """Run comparison command."""
        try:
            # Load experimental data
            data = self.data_loader.load_data(args.file)
            print(f"Loaded {len(data)} experimental records")
            
            if args.simulate:
                # Run comparison simulations
                comparison = self.simulator.compare_with_experimental(data)
                
                print(f"\\nComparison Results:")
                print(f"  Correlation coefficient: {comparison.correlation_coefficient:.3f}")
                print(f"  Mean absolute error: {comparison.mean_absolute_error:.2f} Gy")
                print(f"  Relative error: {comparison.relative_error:.1f}%")
                print(f"  Number of comparisons: {comparison.statistics['n_comparisons']}")
                
                # Generate comparison plot if requested
                if args.plot:
                    plot_path = "experimental_vs_simulation.png"
                    self.visualizer.plot_experimental_comparison(comparison, plot_path)
                    print(f"\\nComparison plot saved to {plot_path}")
                
                # Save results if requested
                if args.output:
                    output_data = {
                        'correlation': comparison.correlation_coefficient,
                        'mae': comparison.mean_absolute_error,
                        'relative_error': comparison.relative_error,
                        'statistics': comparison.statistics
                    }
                    
                    with open(args.output, 'w') as f:
                        json.dump(output_data, f, indent=2)
                    print(f"\\nComparison results saved to {args.output}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Comparison error: {e}")
            return 1
    
    def run_optimize(self, args) -> int:
        """Run optimization command."""
        try:
            # Create geometry configuration
            if args.geometry == 'sphere':
                geometry_config = {
                    'shape': 'sphere',
                    'dimensions': {'radius': args.geometry_size}
                }
            elif args.geometry == 'cylinder':
                geometry_config = {
                    'shape': 'cylinder',
                    'dimensions': {'radius': args.geometry_size, 'height': args.geometry_size * 2}
                }
            else:  # box
                geometry_config = {
                    'shape': 'box',
                    'dimensions': {
                        'length': args.geometry_size,
                        'width': args.geometry_size,
                        'height': args.geometry_size
                    }
                }
            
            # Run optimization
            optimized_params = self.simulator.optimize_exposure_parameters(
                target_dose=args.target_dose,
                material_name=args.material,
                source_type=args.source,
                source_activity=args.activity,
                source_distance=args.distance,
                geometry_config=geometry_config,
                tolerance=args.tolerance
            )
            
            print(f"\\nOptimization Results:")
            print(f"  Target dose: {args.target_dose:.2f} Gy")
            print(f"  Optimized exposure time: {optimized_params.exposure_time:.2f} hours")
            print(f"  Source: {optimized_params.source.value}")
            print(f"  Material: {optimized_params.material.name}")
            print(f"  Activity: {optimized_params.source_activity:.2f}")
            print(f"  Distance: {optimized_params.source_distance:.2f} cm")
            
            # Save optimized parameters if requested
            if args.output:
                output_data = {
                    'target_dose': args.target_dose,
                    'optimized_parameters': {
                        'source': optimized_params.source.value,
                        'material': optimized_params.material.name,
                        'activity': optimized_params.source_activity,
                        'distance': optimized_params.source_distance,
                        'exposure_time': optimized_params.exposure_time,
                        'geometry': {
                            'shape': optimized_params.geometry.shape,
                            'dimensions': optimized_params.geometry.dimensions
                        }
                    }
                }
                
                with open(args.output, 'w') as f:
                    json.dump(output_data, f, indent=2)
                print(f"\\nOptimized parameters saved to {args.output}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            return 1
    
    def run_config(self, args) -> int:
        """Run configuration command."""
        try:
            if args.create_template:
                template = {
                    "simulation": {
                        "default_source": "Co-60",
                        "default_material": "wheat",
                        "default_geometry": {
                            "shape": "sphere",
                            "dimensions": {"radius": 1.0}
                        },
                        "grid_resolution": 50
                    },
                    "visualization": {
                        "output_directory": "./plots",
                        "save_format": "png",
                        "dpi": 300
                    },
                    "logging": {
                        "level": "INFO",
                        "file": null
                    }
                }
                
                with open(args.create_template, 'w') as f:
                    yaml.dump(template, f, default_flow_style=False, indent=2)
                print(f"Configuration template created: {args.create_template}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Configuration error: {e}")
            return 1
    
    def run(self, args=None) -> int:
        """Run the CLI application."""
        parser = self.create_parser()
        
        if args is None:
            args = parser.parse_args()
        else:
            args = parser.parse_args(args)
        
        # Setup logging
        self.setup_logging(args)
        
        # Route to appropriate command
        if args.command == 'simulate':
            return self.run_simulate(args)
        elif args.command == 'load-data':
            return self.run_load_data(args)
        elif args.command == 'compare':
            return self.run_compare(args)
        elif args.command == 'optimize':
            return self.run_optimize(args)
        elif args.command == 'config':
            return self.run_config(args)
        else:
            parser.print_help()
            return 1


def main():
    """Main entry point for the CLI."""
    cli = CLI()
    return cli.run()


if __name__ == '__main__':
    sys.exit(main())