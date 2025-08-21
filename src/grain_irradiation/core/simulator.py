"""
Core simulation engine for grain irradiation.

This module orchestrates the irradiation simulation process, combining
physics models with experimental data to produce simulation results.
"""

import numpy as np
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import time
from datetime import datetime

from .physics import (
    IrradiationPhysics, RadiationSource, MaterialProperties, 
    GeometryConfig
)
from ..data.loader import ExperimentalData, DataLoader

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class SimulationParameters:
    """Configuration parameters for irradiation simulation."""
    source: RadiationSource
    source_activity: float  # Ci or kW
    source_distance: float  # cm
    exposure_time: float  # hours
    material: MaterialProperties
    geometry: GeometryConfig
    temperature: Optional[float] = None  # °C
    humidity: Optional[float] = None  # %
    grid_resolution: int = 50
    
    def validate(self) -> bool:
        """Validate simulation parameters."""
        checks = [
            self.source_activity > 0,
            self.source_distance > 0,
            self.exposure_time > 0,
            self.grid_resolution > 0
        ]
        return all(checks)


@dataclass
class SimulationResults:
    """Container for simulation results."""
    parameters: SimulationParameters
    uniform_dose: float  # Gy
    max_dose: float  # Gy
    min_dose: float  # Gy
    mean_dose: float  # Gy
    dose_uniformity: float  # min/max ratio
    dose_distribution: Optional[np.ndarray] = None
    coordinates: Optional[Tuple[np.ndarray, np.ndarray]] = None
    computation_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of simulation results."""
        return {
            'uniform_dose_Gy': self.uniform_dose,
            'max_dose_Gy': self.max_dose,
            'min_dose_Gy': self.min_dose,
            'mean_dose_Gy': self.mean_dose,
            'dose_uniformity_ratio': self.dose_uniformity,
            'computation_time_s': self.computation_time,
            'timestamp': self.timestamp
        }


@dataclass
class ComparisonResults:
    """Results of experimental vs simulation comparison."""
    experimental_data: List[ExperimentalData]
    simulation_results: List[SimulationResults]
    correlation_coefficient: float
    mean_absolute_error: float  # Gy
    relative_error: float  # %
    statistics: Dict[str, Any]


class IrradiationSimulator:
    """
    Main simulation engine for grain irradiation processes.
    
    This class combines physics models with experimental data to provide
    comprehensive simulation capabilities for research and education.
    """
    
    def __init__(self):
        """Initialize the simulation engine."""
        self.logger = logging.getLogger(__name__ + ".IrradiationSimulator")
        self.physics = IrradiationPhysics()
        self.data_loader = DataLoader()
        
        # Simulation history
        self.simulation_history: List[SimulationResults] = []
        
        # Default parameters
        self.default_materials = self.physics.standard_materials
        
    def create_simulation_parameters(self, 
                                   source_type: str,
                                   material_name: str,
                                   source_activity: float,
                                   source_distance: float,
                                   exposure_time: float,
                                   geometry_config: Dict[str, Any],
                                   **kwargs) -> SimulationParameters:
        """
        Create simulation parameters from input values.
        
        Args:
            source_type: Type of radiation source (e.g., "Co-60")
            material_name: Name of material (must be in default_materials)
            source_activity: Source activity in appropriate units
            source_distance: Distance from source in cm
            exposure_time: Exposure time in hours
            geometry_config: Dictionary with geometry configuration
            **kwargs: Additional optional parameters
            
        Returns:
            SimulationParameters object
        """
        # Convert source type string to enum
        source_map = {
            "Co-60": RadiationSource.COBALT_60,
            "Cobalt-60": RadiationSource.COBALT_60,
            "Cs-137": RadiationSource.CESIUM_137,
            "Cesium-137": RadiationSource.CESIUM_137,
            "LinAc": RadiationSource.LINEAR_ACCELERATOR,
            "Linear Accelerator": RadiationSource.LINEAR_ACCELERATOR
        }
        
        if source_type not in source_map:
            raise ValueError(f"Unknown source type: {source_type}")
        
        source = source_map[source_type]
        
        # Get material properties
        if material_name not in self.default_materials:
            raise ValueError(f"Unknown material: {material_name}")
        
        material = self.default_materials[material_name]
        
        # Create geometry configuration
        geometry = GeometryConfig(**geometry_config)
        
        # Create parameters
        params = SimulationParameters(
            source=source,
            source_activity=source_activity,
            source_distance=source_distance,
            exposure_time=exposure_time,
            material=material,
            geometry=geometry,
            temperature=kwargs.get('temperature'),
            humidity=kwargs.get('humidity'),
            grid_resolution=kwargs.get('grid_resolution', 50)
        )
        
        if not params.validate():
            raise ValueError("Invalid simulation parameters")
        
        return params
    
    def run_simulation(self, parameters: SimulationParameters, 
                      calculate_distribution: bool = True) -> SimulationResults:
        """
        Run irradiation simulation with given parameters.
        
        Args:
            parameters: Simulation configuration
            calculate_distribution: Whether to calculate spatial dose distribution
            
        Returns:
            SimulationResults object
        """
        start_time = time.time()
        
        self.logger.info(f"Starting simulation with {parameters.source.value} source")
        
        # Validate parameters
        if not self.physics.validate_parameters(
            dose=parameters.source_activity * parameters.exposure_time,
            exposure_time=parameters.exposure_time,
            activity=parameters.source_activity
        ):
            self.logger.warning("Parameter validation failed - proceeding with caution")
        
        # Calculate uniform dose (simplified model)
        uniform_dose = self.physics.calculate_uniform_dose(
            material=parameters.material,
            source=parameters.source,
            activity=parameters.source_activity,
            distance=parameters.source_distance / 100,  # Convert cm to m
            exposure_time=parameters.exposure_time
        )
        
        # Calculate spatial dose distribution if requested
        dose_distribution = None
        coordinates = None
        max_dose = uniform_dose
        min_dose = uniform_dose
        mean_dose = uniform_dose
        
        if calculate_distribution:
            try:
                X, Y, dose_matrix = self.physics.calculate_dose_distribution(
                    geometry=parameters.geometry,
                    material=parameters.material,
                    source=parameters.source,
                    source_distance=parameters.source_distance,
                    activity=parameters.source_activity,
                    exposure_time=parameters.exposure_time,
                    grid_points=parameters.grid_resolution
                )
                
                dose_distribution = dose_matrix
                coordinates = (X, Y)
                
                # Calculate statistics
                valid_doses = dose_matrix[dose_matrix > 0]
                if len(valid_doses) > 0:
                    max_dose = np.max(valid_doses)
                    min_dose = np.min(valid_doses)
                    mean_dose = np.mean(valid_doses)
                
            except Exception as e:
                self.logger.error(f"Error calculating dose distribution: {e}")
                # Continue with uniform dose calculations
        
        # Calculate dose uniformity
        dose_uniformity = min_dose / max_dose if max_dose > 0 else 0
        
        computation_time = time.time() - start_time
        
        # Create results
        results = SimulationResults(
            parameters=parameters,
            uniform_dose=uniform_dose,
            max_dose=max_dose,
            min_dose=min_dose,
            mean_dose=mean_dose,
            dose_uniformity=dose_uniformity,
            dose_distribution=dose_distribution,
            coordinates=coordinates,
            computation_time=computation_time
        )
        
        # Store in history
        self.simulation_history.append(results)
        
        self.logger.info(f"Simulation completed in {computation_time:.2f}s - "
                        f"Mean dose: {mean_dose:.2f} Gy")
        
        return results
    
    def run_batch_simulation(self, 
                           parameter_sets: List[SimulationParameters]) -> List[SimulationResults]:
        """
        Run multiple simulations with different parameters.
        
        Args:
            parameter_sets: List of simulation parameters
            
        Returns:
            List of simulation results
        """
        results = []
        
        self.logger.info(f"Starting batch simulation with {len(parameter_sets)} parameter sets")
        
        for i, params in enumerate(parameter_sets):
            self.logger.info(f"Running simulation {i+1}/{len(parameter_sets)}")
            
            try:
                result = self.run_simulation(params, calculate_distribution=False)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error in simulation {i+1}: {e}")
                continue
        
        self.logger.info(f"Batch simulation completed: {len(results)} successful simulations")
        return results
    
    def compare_with_experimental(self, 
                                experimental_data: List[ExperimentalData],
                                simulation_tolerance: float = 0.1) -> ComparisonResults:
        """
        Compare simulation results with experimental data.
        
        Args:
            experimental_data: List of experimental measurements
            simulation_tolerance: Tolerance for parameter matching
            
        Returns:
            ComparisonResults object
        """
        self.logger.info(f"Comparing simulations with {len(experimental_data)} experimental records")
        
        simulation_results = []
        experimental_doses = []
        simulated_doses = []
        
        for exp_data in experimental_data:
            try:
                # Create simulation parameters from experimental data
                params = self.create_simulation_parameters(
                    source_type=exp_data.source_type,
                    material_name=exp_data.material,
                    source_activity=exp_data.source_activity,
                    source_distance=exp_data.distance,
                    exposure_time=exp_data.exposure_time,
                    geometry_config={
                        "shape": "sphere",
                        "dimensions": {"radius": 1.0}  # Default geometry
                    },
                    temperature=exp_data.temperature,
                    humidity=exp_data.humidity
                )
                
                # Run simulation
                result = self.run_simulation(params, calculate_distribution=False)
                simulation_results.append(result)
                
                experimental_doses.append(exp_data.dose)
                simulated_doses.append(result.uniform_dose)
                
            except Exception as e:
                self.logger.warning(f"Could not simulate for experimental data {exp_data.sample_id}: {e}")
                continue
        
        if not experimental_doses:
            raise ValueError("No valid experimental data for comparison")
        
        # Calculate comparison statistics
        exp_doses = np.array(experimental_doses)
        sim_doses = np.array(simulated_doses)
        
        correlation = np.corrcoef(exp_doses, sim_doses)[0, 1]
        mae = np.mean(np.abs(exp_doses - sim_doses))
        relative_error = np.mean(np.abs((exp_doses - sim_doses) / exp_doses)) * 100
        
        statistics = {
            'n_comparisons': len(experimental_doses),
            'experimental_mean': np.mean(exp_doses),
            'experimental_std': np.std(exp_doses),
            'simulated_mean': np.mean(sim_doses),
            'simulated_std': np.std(sim_doses),
            'bias': np.mean(sim_doses - exp_doses),
            'rmse': np.sqrt(np.mean((exp_doses - sim_doses)**2))
        }
        
        comparison_results = ComparisonResults(
            experimental_data=experimental_data,
            simulation_results=simulation_results,
            correlation_coefficient=correlation,
            mean_absolute_error=mae,
            relative_error=relative_error,
            statistics=statistics
        )
        
        self.logger.info(f"Comparison completed: r={correlation:.3f}, "
                        f"MAE={mae:.2f} Gy, "
                        f"Relative error={relative_error:.1f}%")
        
        return comparison_results
    
    def optimize_exposure_parameters(self, 
                                   target_dose: float,
                                   material_name: str,
                                   source_type: str,
                                   source_activity: float,
                                   source_distance: float,
                                   geometry_config: Dict[str, Any],
                                   tolerance: float = 0.05) -> SimulationParameters:
        """
        Optimize exposure time to achieve target dose.
        
        Args:
            target_dose: Target dose in Gy
            material_name: Material name
            source_type: Source type
            source_activity: Source activity
            source_distance: Source distance in cm
            geometry_config: Geometry configuration
            tolerance: Relative tolerance for target dose
            
        Returns:
            Optimized SimulationParameters
        """
        self.logger.info(f"Optimizing exposure time for target dose: {target_dose:.2f} Gy")
        
        # Initial guess based on uniform dose calculation
        dose_rate = self.physics.calculate_dose_rate(
            source=RadiationSource.COBALT_60 if "Co" in source_type else RadiationSource.CESIUM_137,
            activity=source_activity,
            distance=source_distance / 100
        )
        
        initial_time = target_dose / dose_rate
        
        # Simple iterative optimization
        best_time = initial_time
        best_error = float('inf')
        
        for time_factor in np.linspace(0.5, 2.0, 20):
            test_time = initial_time * time_factor
            
            try:
                params = self.create_simulation_parameters(
                    source_type=source_type,
                    material_name=material_name,
                    source_activity=source_activity,
                    source_distance=source_distance,
                    exposure_time=test_time,
                    geometry_config=geometry_config
                )
                
                result = self.run_simulation(params, calculate_distribution=False)
                error = abs(result.uniform_dose - target_dose) / target_dose
                
                if error < best_error:
                    best_error = error
                    best_time = test_time
                
                if error < tolerance:
                    break
                    
            except Exception as e:
                self.logger.warning(f"Error in optimization iteration: {e}")
                continue
        
        # Create final optimized parameters
        optimized_params = self.create_simulation_parameters(
            source_type=source_type,
            material_name=material_name,
            source_activity=source_activity,
            source_distance=source_distance,
            exposure_time=best_time,
            geometry_config=geometry_config
        )
        
        self.logger.info(f"Optimization completed: exposure time = {best_time:.2f} h, "
                        f"error = {best_error*100:.1f}%")
        
        return optimized_params
    
    def get_simulation_report(self, results: SimulationResults) -> str:
        """
        Generate a text report for simulation results.
        
        Args:
            results: Simulation results
            
        Returns:
            Formatted text report
        """
        report = []
        report.append("=" * 60)
        report.append("GRAIN IRRADIATION SIMULATION REPORT")
        report.append("=" * 60)
        report.append(f"Timestamp: {results.timestamp}")
        report.append(f"Computation time: {results.computation_time:.2f} seconds")
        report.append("")
        
        # Parameters
        report.append("SIMULATION PARAMETERS:")
        report.append("-" * 30)
        params = results.parameters
        report.append(f"Source: {params.source.value}")
        report.append(f"Source activity: {params.source_activity:.2f}")
        report.append(f"Source distance: {params.source_distance:.2f} cm")
        report.append(f"Exposure time: {params.exposure_time:.2f} hours")
        report.append(f"Material: {params.material.name}")
        report.append(f"Material density: {params.material.density:.2f} g/cm³")
        report.append(f"Geometry: {params.geometry.shape}")
        if params.temperature is not None:
            report.append(f"Temperature: {params.temperature:.1f}°C")
        if params.humidity is not None:
            report.append(f"Humidity: {params.humidity:.1f}%")
        report.append("")
        
        # Results
        report.append("SIMULATION RESULTS:")
        report.append("-" * 30)
        report.append(f"Uniform dose: {results.uniform_dose:.2f} Gy")
        report.append(f"Maximum dose: {results.max_dose:.2f} Gy")
        report.append(f"Minimum dose: {results.min_dose:.2f} Gy")
        report.append(f"Mean dose: {results.mean_dose:.2f} Gy")
        report.append(f"Dose uniformity ratio: {results.dose_uniformity:.3f}")
        report.append("")
        
        # Dose classification
        dose_category = self._classify_dose(results.mean_dose)
        report.append(f"Dose category: {dose_category}")
        report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def _classify_dose(self, dose: float) -> str:
        """Classify dose level according to typical food irradiation categories."""
        if dose < 1:
            return "Low dose (< 1 kGy) - Sprouting inhibition, insect disinfestation"
        elif dose < 10:
            return "Medium dose (1-10 kGy) - Pathogen reduction, shelf-life extension"
        elif dose < 50:
            return "High dose (10-50 kGy) - Sterilization, decontamination"
        else:
            return "Very high dose (> 50 kGy) - Research/industrial applications"
    
    def clear_history(self):
        """Clear simulation history."""
        self.simulation_history.clear()
        self.logger.info("Simulation history cleared")
    
    def get_history_summary(self) -> Dict[str, Any]:
        """Get summary of simulation history."""
        if not self.simulation_history:
            return {"total_simulations": 0}
        
        doses = [r.mean_dose for r in self.simulation_history]
        times = [r.computation_time for r in self.simulation_history]
        
        return {
            "total_simulations": len(self.simulation_history),
            "mean_dose_range": [min(doses), max(doses)],
            "mean_computation_time": np.mean(times),
            "last_simulation": self.simulation_history[-1].timestamp
        }