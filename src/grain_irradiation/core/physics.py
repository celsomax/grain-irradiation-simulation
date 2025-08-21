"""
Physics module for grain irradiation simulation.

This module implements the fundamental physical models for radiation dose
calculations, penetration models, and spatial dose distribution.

References:
- Cleland, M. R., & Parks, L. A. (2003). Medium and high-energy electron beam sterilization
- IAEA Technical Document on Food Irradiation (2015)
- Turner, J. E. (2007). Atoms, Radiation, and Radiation Protection
"""

import numpy as np
import logging
from typing import Tuple, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RadiationSource(Enum):
    """Types of radiation sources supported by the simulation."""
    COBALT_60 = "Co-60"
    LINEAR_ACCELERATOR = "LinAc"
    CESIUM_137 = "Cs-137"


@dataclass
class MaterialProperties:
    """Physical properties of the material being irradiated."""
    density: float  # g/cm³
    atomic_number: float  # Effective atomic number
    mass_attenuation_coefficient: float  # cm²/g
    name: str = "Unknown"
    
    def __post_init__(self):
        if self.density <= 0:
            raise ValueError("Density must be positive")
        if self.atomic_number <= 0:
            raise ValueError("Atomic number must be positive")


@dataclass
class GeometryConfig:
    """Configuration for sample geometry."""
    shape: str  # "sphere", "cylinder", "box"
    dimensions: Dict[str, float]  # geometry-specific dimensions
    volume: Optional[float] = None
    
    def __post_init__(self):
        if self.shape not in ["sphere", "cylinder", "box"]:
            raise ValueError(f"Unsupported geometry shape: {self.shape}")
        
        # Calculate volume based on shape
        if self.volume is None:
            self.volume = self._calculate_volume()
    
    def _calculate_volume(self) -> float:
        """Calculate volume based on geometry shape and dimensions."""
        if self.shape == "sphere":
            radius = self.dimensions.get("radius", 1.0)
            return (4/3) * np.pi * radius**3
        elif self.shape == "cylinder":
            radius = self.dimensions.get("radius", 1.0)
            height = self.dimensions.get("height", 1.0)
            return np.pi * radius**2 * height
        elif self.shape == "box":
            length = self.dimensions.get("length", 1.0)
            width = self.dimensions.get("width", 1.0)
            height = self.dimensions.get("height", 1.0)
            return length * width * height
        return 1.0


class IrradiationPhysics:
    """
    Core physics engine for irradiation calculations.
    
    This class implements validated physical models for radiation dose
    calculations including penetration, attenuation, and spatial distribution.
    """
    
    def __init__(self):
        """Initialize the physics engine with default parameters."""
        self.logger = logging.getLogger(__name__ + ".IrradiationPhysics")
        
        # Standard material properties (can be extended)
        self.standard_materials = {
            "wheat": MaterialProperties(
                density=0.8, 
                atomic_number=6.5, 
                mass_attenuation_coefficient=0.0302,
                name="wheat"
            ),
            "rice": MaterialProperties(
                density=0.75, 
                atomic_number=6.3, 
                mass_attenuation_coefficient=0.0298,
                name="rice"
            ),
            "corn": MaterialProperties(
                density=0.85, 
                atomic_number=6.7, 
                mass_attenuation_coefficient=0.0305,
                name="corn"
            ),
            "water": MaterialProperties(
                density=1.0, 
                atomic_number=7.4, 
                mass_attenuation_coefficient=0.0270,
                name="water"
            )
        }
        
        # Radiation source properties
        self.source_properties = {
            RadiationSource.COBALT_60: {
                "energy": 1.25,  # MeV (average of 1.17 and 1.33 MeV)
                "half_life": 5.27,  # years
                "dose_rate_constant": 1.32  # R·m²/(h·Ci)
            },
            RadiationSource.CESIUM_137: {
                "energy": 0.662,  # MeV
                "half_life": 30.1,  # years
                "dose_rate_constant": 0.325  # R·m²/(h·Ci)
            },
            RadiationSource.LINEAR_ACCELERATOR: {
                "energy": 10.0,  # MeV (configurable)
                "pulse_frequency": 300,  # Hz
                "beam_current": 10  # mA
            }
        }
    
    def calculate_dose_rate(self, 
                           source: RadiationSource, 
                           activity: float, 
                           distance: float) -> float:
        """
        Calculate dose rate at a given distance from the source.
        
        Args:
            source: Type of radiation source
            activity: Source activity in Ci (for isotopes) or beam power (for accelerators)
            distance: Distance from source in meters
            
        Returns:
            Dose rate in Gy/h
        """
        if distance <= 0:
            raise ValueError("Distance must be positive")
        if activity <= 0:
            raise ValueError("Activity must be positive")
        
        if source in [RadiationSource.COBALT_60, RadiationSource.CESIUM_137]:
            # For gamma sources: Dose rate ∝ 1/r²
            dose_constant = self.source_properties[source]["dose_rate_constant"]
            # Convert from R/h to Gy/h (1 R ≈ 0.00877 Gy for air)
            dose_rate = (dose_constant * activity * 0.00877) / (distance**2)
        else:
            # For electron beams (simplified model)
            beam_power = activity  # Assuming activity represents beam power in kW
            dose_rate = (beam_power * 1000) / (4 * np.pi * distance**2)  # Simplified
        
        self.logger.info(f"Calculated dose rate: {dose_rate:.4f} Gy/h at {distance:.2f} m")
        return dose_rate
    
    def calculate_attenuation(self, 
                             material: MaterialProperties, 
                             thickness: float, 
                             energy: float) -> float:
        """
        Calculate radiation attenuation through material using Beer-Lambert law.
        
        Args:
            material: Material properties
            thickness: Material thickness in cm
            energy: Radiation energy in MeV
            
        Returns:
            Transmission factor (0-1)
        """
        if thickness < 0:
            raise ValueError("Thickness cannot be negative")
        
        # Energy-dependent mass attenuation coefficient (simplified model)
        mu_mass = material.mass_attenuation_coefficient * (1.25 / energy)**0.5
        mu_linear = mu_mass * material.density
        
        transmission = np.exp(-mu_linear * thickness)
        
        self.logger.debug(f"Attenuation through {thickness:.2f} cm of {material.name}: "
                         f"{transmission:.4f}")
        return transmission
    
    def calculate_dose_distribution(self, 
                                  geometry: GeometryConfig,
                                  material: MaterialProperties,
                                  source: RadiationSource,
                                  source_distance: float,
                                  activity: float,
                                  exposure_time: float,
                                  grid_points: int = 50) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate 3D dose distribution within the sample.
        
        Args:
            geometry: Sample geometry configuration
            material: Material properties
            source: Radiation source type
            source_distance: Distance from source to sample surface in cm
            activity: Source activity
            exposure_time: Exposure time in hours
            grid_points: Number of grid points for calculation
            
        Returns:
            Tuple of (x_coords, y_coords, dose_matrix) for visualization
        """
        energy = self.source_properties[source]["energy"]
        
        # Create coordinate grids based on geometry
        if geometry.shape == "sphere":
            radius = geometry.dimensions["radius"]
            x = np.linspace(-radius, radius, grid_points)
            y = np.linspace(-radius, radius, grid_points)
        elif geometry.shape == "cylinder":
            radius = geometry.dimensions["radius"]
            x = np.linspace(-radius, radius, grid_points)
            y = np.linspace(-radius, radius, grid_points)
        else:  # box
            length = geometry.dimensions["length"]
            width = geometry.dimensions["width"]
            x = np.linspace(-length/2, length/2, grid_points)
            y = np.linspace(-width/2, width/2, grid_points)
        
        X, Y = np.meshgrid(x, y)
        dose_matrix = np.zeros_like(X)
        
        # Calculate dose at each point
        for i in range(grid_points):
            for j in range(grid_points):
                # Distance from source to this point
                point_distance = np.sqrt((source_distance + X[i,j])**2 + Y[i,j]**2)
                
                # Check if point is inside the geometry
                if self._point_inside_geometry(X[i,j], Y[i,j], geometry):
                    # Calculate path length through material to this point
                    path_length = self._calculate_path_length(X[i,j], Y[i,j], geometry)
                    
                    # Initial dose rate at sample surface
                    dose_rate = self.calculate_dose_rate(source, activity, point_distance/100)  # Convert to meters
                    
                    # Apply attenuation
                    transmission = self.calculate_attenuation(material, path_length, energy)
                    
                    # Final dose
                    dose_matrix[i,j] = dose_rate * transmission * exposure_time
        
        self.logger.info(f"Calculated dose distribution with max dose: "
                        f"{np.max(dose_matrix):.2f} Gy")
        
        return X, Y, dose_matrix
    
    def _point_inside_geometry(self, x: float, y: float, geometry: GeometryConfig) -> bool:
        """Check if a point is inside the given geometry."""
        if geometry.shape == "sphere":
            radius = geometry.dimensions["radius"]
            return x**2 + y**2 <= radius**2
        elif geometry.shape == "cylinder":
            radius = geometry.dimensions["radius"]
            return x**2 + y**2 <= radius**2
        else:  # box
            length = geometry.dimensions["length"]
            width = geometry.dimensions["width"]
            return abs(x) <= length/2 and abs(y) <= width/2
    
    def _calculate_path_length(self, x: float, y: float, geometry: GeometryConfig) -> float:
        """Calculate path length from surface to point inside geometry."""
        if geometry.shape == "sphere":
            radius = geometry.dimensions["radius"]
            return radius - np.sqrt(x**2 + y**2)
        elif geometry.shape == "cylinder":
            radius = geometry.dimensions["radius"]
            return radius - np.sqrt(x**2 + y**2)
        else:  # box
            length = geometry.dimensions["length"]
            return length/2 + x  # Simplified: assume beam from one side
    
    def calculate_uniform_dose(self, 
                              material: MaterialProperties,
                              source: RadiationSource,
                              activity: float,
                              distance: float,
                              exposure_time: float) -> float:
        """
        Calculate uniform dose for simplified calculations.
        
        Args:
            material: Material properties
            source: Radiation source
            activity: Source activity
            distance: Distance to sample in meters
            exposure_time: Exposure time in hours
            
        Returns:
            Total dose in Gy
        """
        dose_rate = self.calculate_dose_rate(source, activity, distance)
        total_dose = dose_rate * exposure_time
        
        self.logger.info(f"Calculated uniform dose: {total_dose:.2f} Gy")
        return total_dose
    
    def validate_parameters(self, **kwargs) -> bool:
        """Validate input parameters for physical reasonableness."""
        validations = []
        
        if 'dose' in kwargs:
            dose = kwargs['dose']
            # Typical food irradiation doses: 0.1 - 10 kGy
            validations.append(0.1 <= dose <= 10000)
        
        if 'exposure_time' in kwargs:
            time = kwargs['exposure_time']
            # Reasonable exposure times: minutes to hours
            validations.append(0.001 <= time <= 24)
        
        if 'activity' in kwargs:
            activity = kwargs['activity']
            # Reasonable source activities
            validations.append(0.1 <= activity <= 10000)
        
        is_valid = all(validations)
        if not is_valid:
            self.logger.warning("Parameter validation failed")
        
        return is_valid