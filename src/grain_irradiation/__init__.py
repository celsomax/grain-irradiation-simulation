# Package initialization for grain_irradiation
__version__ = "0.1.0"
__author__ = "Grain Irradiation Simulation Team"
__description__ = "A Python software for simulating grain and seed irradiation processes"

from .core.physics import IrradiationPhysics
from .core.simulator import IrradiationSimulator
from .core.models import GrainIrradiationModels
from .data.loader import DataLoader
from .visualization.plotter import DoseVisualizer

# Create alias for the main class as specified in requirements
GrainIrradiationSimulator = IrradiationSimulator

__all__ = [
    "IrradiationPhysics",
    "IrradiationSimulator", 
    "GrainIrradiationSimulator",  # Alias for compatibility
    "GrainIrradiationModels",
    "DataLoader",
    "DoseVisualizer"
]