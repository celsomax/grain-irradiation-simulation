"""
Unit tests for the grain irradiation simulation package.

This module contains comprehensive tests for all core functionality
including physics calculations, data loading, and simulation engine.
"""

import unittest
import numpy as np
import tempfile
import json
import csv
from pathlib import Path

from src.grain_irradiation.core.physics import (
    IrradiationPhysics, RadiationSource, MaterialProperties, GeometryConfig
)
from src.grain_irradiation.core.simulator import IrradiationSimulator, SimulationParameters
from src.grain_irradiation.data.loader import DataLoader, ExperimentalData


class TestIrradiationPhysics(unittest.TestCase):
    """Test cases for the IrradiationPhysics class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.physics = IrradiationPhysics()
        self.test_material = MaterialProperties(
            density=0.8,
            atomic_number=6.5,
            mass_attenuation_coefficient=0.0302,
            name="test_material"
        )
        self.test_geometry = GeometryConfig(
            shape="sphere",
            dimensions={"radius": 1.0}
        )
    
    def test_dose_rate_calculation(self):
        """Test dose rate calculations for different sources."""
        # Test Co-60 source
        dose_rate = self.physics.calculate_dose_rate(
            source=RadiationSource.COBALT_60,
            activity=1000,  # Ci
            distance=1.0   # m
        )
        self.assertGreater(dose_rate, 0)
        self.assertIsInstance(dose_rate, float)
        
        # Test distance scaling (inverse square law)
        dose_rate_2m = self.physics.calculate_dose_rate(
            source=RadiationSource.COBALT_60,
            activity=1000,
            distance=2.0
        )
        self.assertAlmostEqual(dose_rate / dose_rate_2m, 4.0, places=1)
    
    def test_attenuation_calculation(self):
        """Test radiation attenuation calculations."""
        # Test attenuation through material
        transmission = self.physics.calculate_attenuation(
            material=self.test_material,
            thickness=1.0,  # cm
            energy=1.25     # MeV
        )
        
        self.assertGreater(transmission, 0)
        self.assertLessEqual(transmission, 1)
        
        # Test that thicker material attenuates more
        thick_transmission = self.physics.calculate_attenuation(
            material=self.test_material,
            thickness=5.0,
            energy=1.25
        )
        self.assertLess(thick_transmission, transmission)
    
    def test_dose_distribution_calculation(self):
        """Test spatial dose distribution calculations."""
        X, Y, dose_matrix = self.physics.calculate_dose_distribution(
            geometry=self.test_geometry,
            material=self.test_material,
            source=RadiationSource.COBALT_60,
            source_distance=50,  # cm
            activity=1000,
            exposure_time=2.0,
            grid_points=10
        )
        
        # Check array shapes
        self.assertEqual(X.shape, (10, 10))
        self.assertEqual(Y.shape, (10, 10))
        self.assertEqual(dose_matrix.shape, (10, 10))
        
        # Check that dose values are non-negative
        self.assertTrue(np.all(dose_matrix >= 0))
        
        # Check that maximum dose is greater than zero
        self.assertGreater(np.max(dose_matrix), 0)
    
    def test_parameter_validation(self):
        """Test parameter validation."""
        # Valid parameters
        self.assertTrue(self.physics.validate_parameters(
            dose=5.0,
            exposure_time=2.0,
            activity=1000
        ))
        
        # Invalid parameters
        self.assertFalse(self.physics.validate_parameters(
            dose=-1.0,  # Negative dose
            exposure_time=2.0,
            activity=1000
        ))
    
    def test_material_properties(self):
        """Test MaterialProperties validation."""
        # Valid material
        material = MaterialProperties(
            density=1.0,
            atomic_number=7.0,
            mass_attenuation_coefficient=0.03,
            name="test"
        )
        self.assertEqual(material.density, 1.0)
        
        # Invalid material (negative density)
        with self.assertRaises(ValueError):
            MaterialProperties(
                density=-1.0,
                atomic_number=7.0,
                mass_attenuation_coefficient=0.03,
                name="invalid"
            )
    
    def test_geometry_config(self):
        """Test GeometryConfig functionality."""
        # Sphere geometry
        sphere = GeometryConfig(
            shape="sphere",
            dimensions={"radius": 2.0}
        )
        expected_volume = (4/3) * np.pi * 8.0  # r^3 = 8
        self.assertAlmostEqual(sphere.volume, expected_volume, places=3)
        
        # Cylinder geometry
        cylinder = GeometryConfig(
            shape="cylinder",
            dimensions={"radius": 1.0, "height": 2.0}
        )
        expected_volume = np.pi * 1.0 * 2.0
        self.assertAlmostEqual(cylinder.volume, expected_volume, places=3)
        
        # Invalid geometry
        with self.assertRaises(ValueError):
            GeometryConfig(
                shape="invalid_shape",
                dimensions={"radius": 1.0}
            )


class TestDataLoader(unittest.TestCase):
    """Test cases for the DataLoader class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.data_loader = DataLoader()
        
        # Create test data
        self.test_data = [
            {
                'sample_id': 'TEST001',
                'material': 'wheat',
                'dose': 5.0,
                'dose_rate': 2.5,
                'exposure_time': 2.0,
                'source_type': 'Co-60',
                'source_activity': 1000,
                'distance': 50,
                'temperature': 25,
                'humidity': 65
            },
            {
                'sample_id': 'TEST002',
                'material': 'rice',
                'dose': 3.0,
                'dose_rate': 1.5,
                'exposure_time': 2.0,
                'source_type': 'Cs-137',
                'source_activity': 800,
                'distance': 60,
                'temperature': 20,
                'humidity': 70
            }
        ]
    
    def test_experimental_data_creation(self):
        """Test ExperimentalData object creation and validation."""
        # Valid data
        exp_data = ExperimentalData(
            sample_id='TEST001',
            material='wheat',
            dose=5.0,
            dose_rate=2.5,
            exposure_time=2.0,
            source_type='Co-60',
            source_activity=1000,
            distance=50
        )
        self.assertEqual(exp_data.sample_id, 'TEST001')
        self.assertEqual(exp_data.dose, 5.0)
        
        # Invalid data (negative dose)
        with self.assertRaises(ValueError):
            ExperimentalData(
                sample_id='INVALID',
                material='wheat',
                dose=-1.0,  # Invalid
                dose_rate=2.5,
                exposure_time=2.0,
                source_type='Co-60',
                source_activity=1000,
                distance=50
            )
    
    def test_csv_loading(self):
        """Test loading data from CSV file."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(f, fieldnames=self.test_data[0].keys())
            writer.writeheader()
            writer.writerows(self.test_data)
            csv_file = f.name
        
        try:
            # Load data
            loaded_data = self.data_loader.load_data(csv_file)
            
            self.assertEqual(len(loaded_data), 2)
            self.assertEqual(loaded_data[0].sample_id, 'TEST001')
            self.assertEqual(loaded_data[1].material, 'rice')
            
        finally:
            Path(csv_file).unlink()  # Clean up
    
    def test_json_loading(self):
        """Test loading data from JSON file."""
        # Create temporary JSON file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.test_data, f)
            json_file = f.name
        
        try:
            # Load data
            loaded_data = self.data_loader.load_data(json_file)
            
            self.assertEqual(len(loaded_data), 2)
            self.assertEqual(loaded_data[0].sample_id, 'TEST001')
            
        finally:
            Path(json_file).unlink()  # Clean up
    
    def test_data_validation(self):
        """Test data validation functionality."""
        # Create test experimental data
        test_exp_data = [
            ExperimentalData(
                sample_id='VALID001',
                material='wheat',
                dose=5.0,
                dose_rate=2.5,
                exposure_time=2.0,
                source_type='Co-60',
                source_activity=1000,
                distance=50
            ),
            ExperimentalData(
                sample_id='WARNING001',
                material='wheat',
                dose=100.0,  # Will trigger warning (unusual dose)
                dose_rate=50.0,
                exposure_time=2.0,
                source_type='Co-60',
                source_activity=1000,
                distance=50
            )
        ]
        
        validation_result = self.data_loader.validate_data(test_exp_data)
        
        self.assertEqual(validation_result.total_records, 2)
        self.assertEqual(validation_result.valid_records, 2)  # Both are valid despite warnings
        self.assertGreater(len(validation_result.warnings), 0)  # Should have warnings
    
    def test_data_filtering(self):
        """Test data filtering functionality."""
        # Create test data
        exp_data = [
            ExperimentalData(
                sample_id='FILTER001',
                material='wheat',
                dose=5.0,
                dose_rate=2.5,
                exposure_time=2.0,
                source_type='Co-60',
                source_activity=1000,
                distance=50
            ),
            ExperimentalData(
                sample_id='FILTER002',
                material='rice',
                dose=10.0,
                dose_rate=5.0,
                exposure_time=2.0,
                source_type='Co-60',
                source_activity=1000,
                distance=50
            )
        ]
        
        # Filter by material
        wheat_data = self.data_loader.filter_data(exp_data, material='wheat')
        self.assertEqual(len(wheat_data), 1)
        self.assertEqual(wheat_data[0].material, 'wheat')
        
        # Filter by dose range
        high_dose_data = self.data_loader.filter_data(exp_data, dose_min=7.0)
        self.assertEqual(len(high_dose_data), 1)
        self.assertEqual(high_dose_data[0].sample_id, 'FILTER002')
    
    def test_summary_statistics(self):
        """Test summary statistics calculation."""
        # Create test data
        exp_data = [
            ExperimentalData(
                sample_id='STAT001',
                material='wheat',
                dose=5.0,
                dose_rate=2.5,
                exposure_time=2.0,
                source_type='Co-60',
                source_activity=1000,
                distance=50
            ),
            ExperimentalData(
                sample_id='STAT002',
                material='wheat',
                dose=10.0,
                dose_rate=5.0,
                exposure_time=2.0,
                source_type='Co-60',
                source_activity=1000,
                distance=50
            )
        ]
        
        summary = self.data_loader.get_summary_statistics(exp_data)
        
        self.assertEqual(summary['total_records'], 2)
        self.assertEqual(summary['dose_statistics']['mean'], 7.5)
        self.assertEqual(summary['dose_statistics']['min'], 5.0)
        self.assertEqual(summary['dose_statistics']['max'], 10.0)
        self.assertIn('wheat', summary['material_distribution'])


class TestIrradiationSimulator(unittest.TestCase):
    """Test cases for the IrradiationSimulator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.simulator = IrradiationSimulator()
    
    def test_simulation_parameters_creation(self):
        """Test creation of simulation parameters."""
        params = self.simulator.create_simulation_parameters(
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
        
        self.assertEqual(params.source, RadiationSource.COBALT_60)
        self.assertEqual(params.material.name, "wheat")
        self.assertEqual(params.source_activity, 1000)
        self.assertTrue(params.validate())
    
    def test_simulation_execution(self):
        """Test running a basic simulation."""
        params = self.simulator.create_simulation_parameters(
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
        
        results = self.simulator.run_simulation(params, calculate_distribution=False)
        
        self.assertGreater(results.uniform_dose, 0)
        self.assertGreater(results.computation_time, 0)
        self.assertIsNotNone(results.timestamp)
    
    def test_batch_simulation(self):
        """Test running multiple simulations."""
        params_list = []
        for activity in [500, 1000, 1500]:
            params = self.simulator.create_simulation_parameters(
                source_type="Co-60",
                material_name="wheat",
                source_activity=activity,
                source_distance=50,
                exposure_time=2.0,
                geometry_config={
                    "shape": "sphere",
                    "dimensions": {"radius": 1.0}
                }
            )
            params_list.append(params)
        
        results_list = self.simulator.run_batch_simulation(params_list)
        
        self.assertEqual(len(results_list), 3)
        # Higher activity should result in higher dose
        self.assertLess(results_list[0].uniform_dose, results_list[2].uniform_dose)
    
    def test_exposure_optimization(self):
        """Test exposure time optimization."""
        target_dose = 5.0
        
        optimized_params = self.simulator.optimize_exposure_parameters(
            target_dose=target_dose,
            material_name="wheat",
            source_type="Co-60",
            source_activity=1000,
            source_distance=50,
            geometry_config={
                "shape": "sphere",
                "dimensions": {"radius": 1.0}
            }
        )
        
        # Run simulation with optimized parameters
        results = self.simulator.run_simulation(optimized_params, calculate_distribution=False)
        
        # Check if dose is close to target (within 10% tolerance)
        relative_error = abs(results.uniform_dose - target_dose) / target_dose
        self.assertLess(relative_error, 0.1)
    
    def test_experimental_comparison(self):
        """Test comparison with experimental data."""
        # Create mock experimental data
        exp_data = [
            ExperimentalData(
                sample_id='COMP001',
                material='wheat',
                dose=5.0,
                dose_rate=2.5,
                exposure_time=2.0,
                source_type='Co-60',
                source_activity=1000,
                distance=50
            )
        ]
        
        comparison = self.simulator.compare_with_experimental(exp_data)
        
        self.assertEqual(len(comparison.experimental_data), 1)
        self.assertEqual(len(comparison.simulation_results), 1)
        self.assertIsInstance(comparison.correlation_coefficient, float)
        self.assertIsInstance(comparison.mean_absolute_error, float)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete simulation workflow."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.simulator = IrradiationSimulator()
        self.data_loader = DataLoader()
    
    def test_complete_workflow(self):
        """Test a complete simulation workflow."""
        # 1. Create simulation parameters
        params = self.simulator.create_simulation_parameters(
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
        
        # 2. Run simulation
        results = self.simulator.run_simulation(params, calculate_distribution=True)
        
        # 3. Validate results
        self.assertGreater(results.uniform_dose, 0)
        self.assertIsNotNone(results.dose_distribution)
        self.assertIsNotNone(results.coordinates)
        
        # 4. Check dose uniformity
        self.assertGreaterEqual(results.dose_uniformity, 0)
        self.assertLessEqual(results.dose_uniformity, 1)
        
        # 5. Generate report
        report = self.simulator.get_simulation_report(results)
        self.assertIsInstance(report, str)
        self.assertIn("SIMULATION REPORT", report)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)