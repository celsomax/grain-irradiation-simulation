"""
Data loading and validation module for experimental data.

This module handles loading, validation, and preprocessing of experimental
irradiation data from various file formats (CSV, JSON, etc.).
"""

import pandas as pd
import numpy as np
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
import yaml

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class ExperimentalData:
    """Container for experimental irradiation data."""
    sample_id: str
    material: str
    dose: float  # Gy
    dose_rate: float  # Gy/h
    exposure_time: float  # hours
    source_type: str
    source_activity: float
    distance: float  # cm
    temperature: Optional[float] = None  # °C
    humidity: Optional[float] = None  # %
    notes: Optional[str] = None
    operator: Optional[str] = None
    date: Optional[str] = None
    equipment: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Validate data after initialization."""
        if self.dose <= 0:
            raise ValueError(f"Dose must be positive, got {self.dose}")
        if self.dose_rate <= 0:
            raise ValueError(f"Dose rate must be positive, got {self.dose_rate}")
        if self.exposure_time <= 0:
            raise ValueError(f"Exposure time must be positive, got {self.exposure_time}")
        if self.distance <= 0:
            raise ValueError(f"Distance must be positive, got {self.distance}")


@dataclass
class DataValidationResult:
    """Result of data validation process."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    valid_records: int
    total_records: int
    
    @property
    def validation_rate(self) -> float:
        """Calculate percentage of valid records."""
        return (self.valid_records / self.total_records * 100) if self.total_records > 0 else 0


class DataLoader:
    """
    Main class for loading and validating experimental data.
    
    Supports multiple file formats and provides validation capabilities
    for ensuring data quality and scientific consistency.
    """
    
    def __init__(self):
        """Initialize the data loader."""
        self.logger = logging.getLogger(__name__ + ".DataLoader")
        self.supported_formats = ['.csv', '.json', '.xlsx', '.yaml', '.yml']
        
        # Define expected columns and their data types
        self.required_columns = {
            'sample_id': str,
            'material': str,
            'dose': float,
            'dose_rate': float,
            'exposure_time': float,
            'source_type': str,
            'source_activity': float,
            'distance': float
        }
        
        self.optional_columns = {
            'temperature': float,
            'humidity': float,
            'notes': str,
            'operator': str,
            'date': str,
            'equipment': str
        }
    
    def load_data(self, file_path: Union[str, Path]) -> List[ExperimentalData]:
        """
        Load experimental data from file.
        
        Args:
            file_path: Path to the data file
            
        Returns:
            List of ExperimentalData objects
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")
        
        if file_path.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        
        self.logger.info(f"Loading data from: {file_path}")
        
        try:
            if file_path.suffix.lower() == '.csv':
                return self._load_csv(file_path)
            elif file_path.suffix.lower() == '.json':
                return self._load_json(file_path)
            elif file_path.suffix.lower() == '.xlsx':
                return self._load_excel(file_path)
            elif file_path.suffix.lower() in ['.yaml', '.yml']:
                return self._load_yaml(file_path)
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            raise
    
    def _load_csv(self, file_path: Path) -> List[ExperimentalData]:
        """Load data from CSV file."""
        df = pd.read_csv(file_path)
        return self._dataframe_to_experimental_data(df)
    
    def _load_json(self, file_path: Path) -> List[ExperimentalData]:
        """Load data from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            # List of records
            return [self._dict_to_experimental_data(record) for record in data]
        elif isinstance(data, dict) and 'experiments' in data:
            # Structured JSON with experiments key
            return [self._dict_to_experimental_data(record) for record in data['experiments']]
        else:
            raise ValueError("Invalid JSON structure")
    
    def _load_excel(self, file_path: Path) -> List[ExperimentalData]:
        """Load data from Excel file."""
        df = pd.read_excel(file_path)
        return self._dataframe_to_experimental_data(df)
    
    def _load_yaml(self, file_path: Path) -> List[ExperimentalData]:
        """Load data from YAML file."""
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if isinstance(data, list):
            return [self._dict_to_experimental_data(record) for record in data]
        elif isinstance(data, dict) and 'experiments' in data:
            return [self._dict_to_experimental_data(record) for record in data['experiments']]
        else:
            raise ValueError("Invalid YAML structure")
    
    def _dataframe_to_experimental_data(self, df: pd.DataFrame) -> List[ExperimentalData]:
        """Convert pandas DataFrame to ExperimentalData objects."""
        experimental_data = []
        
        for _, row in df.iterrows():
            try:
                data = self._dict_to_experimental_data(row.to_dict())
                experimental_data.append(data)
            except Exception as e:
                self.logger.warning(f"Skipping invalid row: {e}")
                continue
        
        return experimental_data
    
    def _dict_to_experimental_data(self, data_dict: Dict[str, Any]) -> ExperimentalData:
        """Convert dictionary to ExperimentalData object."""
        # Extract required fields
        required_data = {}
        for col, dtype in self.required_columns.items():
            if col not in data_dict:
                raise ValueError(f"Missing required column: {col}")
            
            value = data_dict[col]
            if pd.isna(value):
                raise ValueError(f"Missing value for required column: {col}")
            
            # Type conversion
            if dtype == float:
                required_data[col] = float(value)
            elif dtype == str:
                required_data[col] = str(value)
            else:
                required_data[col] = value
        
        # Extract optional fields
        optional_data = {}
        for col, dtype in self.optional_columns.items():
            if col in data_dict and not pd.isna(data_dict[col]):
                if dtype == float:
                    optional_data[col] = float(data_dict[col])
                elif dtype == str:
                    optional_data[col] = str(data_dict[col])
                else:
                    optional_data[col] = data_dict[col]
        
        # Create metadata from remaining fields
        metadata = {}
        for key, value in data_dict.items():
            if (key not in self.required_columns and 
                key not in self.optional_columns and 
                not pd.isna(value)):
                metadata[key] = value
        
        return ExperimentalData(
            **required_data,
            **optional_data,
            metadata=metadata if metadata else None
        )
    
    def validate_data(self, data: List[ExperimentalData]) -> DataValidationResult:
        """
        Validate experimental data for scientific consistency.
        
        Args:
            data: List of ExperimentalData objects
            
        Returns:
            DataValidationResult with validation details
        """
        errors = []
        warnings = []
        valid_count = 0
        total_count = len(data)
        
        for i, experiment in enumerate(data):
            record_errors = []
            record_warnings = []
            
            # Physical consistency checks
            try:
                # Check dose calculation consistency
                calculated_dose = experiment.dose_rate * experiment.exposure_time
                dose_difference = abs(calculated_dose - experiment.dose) / experiment.dose
                
                if dose_difference > 0.1:  # 10% tolerance
                    record_warnings.append(
                        f"Dose calculation inconsistency: "
                        f"calculated {calculated_dose:.2f} Gy vs reported {experiment.dose:.2f} Gy"
                    )
                
                # Check reasonable dose ranges for food irradiation
                if experiment.dose < 0.01 or experiment.dose > 50:  # 0.01 Gy to 50 Gy (more reasonable upper threshold)
                    record_warnings.append(f"Unusual dose value: {experiment.dose:.2f} Gy")
                
                # Check exposure time reasonableness
                if experiment.exposure_time > 48:  # More than 48 hours
                    record_warnings.append(f"Very long exposure time: {experiment.exposure_time:.2f} h")
                
                # Check source activity reasonableness
                if experiment.source_activity > 50000:  # Very high activity
                    record_warnings.append(f"Very high source activity: {experiment.source_activity}")
                
                # Check distance reasonableness
                if experiment.distance < 1 or experiment.distance > 1000:  # 1 cm to 10 m
                    record_warnings.append(f"Unusual distance: {experiment.distance:.2f} cm")
                
                # Temperature checks
                if experiment.temperature is not None:
                    if experiment.temperature < -50 or experiment.temperature > 100:
                        record_warnings.append(f"Extreme temperature: {experiment.temperature:.1f}°C")
                
                # Humidity checks
                if experiment.humidity is not None:
                    if experiment.humidity < 0 or experiment.humidity > 100:
                        record_errors.append(f"Invalid humidity: {experiment.humidity:.1f}%")
                
                if not record_errors:
                    valid_count += 1
                
                # Log issues for this record
                if record_errors:
                    errors.extend([f"Record {i+1}: {err}" for err in record_errors])
                if record_warnings:
                    warnings.extend([f"Record {i+1}: {warn}" for warn in record_warnings])
                    
            except Exception as e:
                errors.append(f"Record {i+1}: Validation error - {e}")
        
        result = DataValidationResult(
            is_valid=(len(errors) == 0),
            errors=errors,
            warnings=warnings,
            valid_records=valid_count,
            total_records=total_count
        )
        
        self.logger.info(f"Validation complete: {result.valid_records}/{result.total_records} "
                        f"valid records ({result.validation_rate:.1f}%)")
        
        if errors:
            self.logger.error(f"Found {len(errors)} validation errors")
        if warnings:
            self.logger.warning(f"Found {len(warnings)} validation warnings")
        
        return result
    
    def save_data(self, data: List[ExperimentalData], file_path: Union[str, Path], 
                  format: str = "csv") -> None:
        """
        Save experimental data to file.
        
        Args:
            data: List of ExperimentalData objects
            file_path: Output file path
            format: Output format ('csv', 'json', 'excel')
        """
        file_path = Path(file_path)
        
        # Convert to DataFrame for easier saving
        df_data = []
        for exp in data:
            row = {
                'sample_id': exp.sample_id,
                'material': exp.material,
                'dose': exp.dose,
                'dose_rate': exp.dose_rate,
                'exposure_time': exp.exposure_time,
                'source_type': exp.source_type,
                'source_activity': exp.source_activity,
                'distance': exp.distance,
                'temperature': exp.temperature,
                'humidity': exp.humidity
            }
            
            # Add metadata
            if exp.metadata:
                row.update(exp.metadata)
            
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        
        if format.lower() == 'csv':
            df.to_csv(file_path, index=False)
        elif format.lower() == 'json':
            df.to_json(file_path, orient='records', indent=2)
        elif format.lower() in ['excel', 'xlsx']:
            df.to_excel(file_path, index=False)
        else:
            raise ValueError(f"Unsupported output format: {format}")
        
        self.logger.info(f"Saved {len(data)} records to {file_path}")
    
    def filter_data(self, data: List[ExperimentalData], **filters) -> List[ExperimentalData]:
        """
        Filter experimental data based on criteria.
        
        Args:
            data: List of ExperimentalData objects
            **filters: Filter criteria (e.g., material='wheat', dose_min=1.0)
            
        Returns:
            Filtered list of ExperimentalData objects
        """
        filtered_data = data.copy()
        
        for filter_name, filter_value in filters.items():
            if filter_name.endswith('_min'):
                field = filter_name[:-4]
                filtered_data = [d for d in filtered_data 
                               if getattr(d, field, 0) >= filter_value]
            elif filter_name.endswith('_max'):
                field = filter_name[:-4]
                filtered_data = [d for d in filtered_data 
                               if getattr(d, field, float('inf')) <= filter_value]
            else:
                filtered_data = [d for d in filtered_data 
                               if getattr(d, filter_name, None) == filter_value]
        
        self.logger.info(f"Filtered data: {len(filtered_data)} records from {len(data)}")
        return filtered_data
    
    def get_summary_statistics(self, data: List[ExperimentalData]) -> Dict[str, Any]:
        """
        Calculate summary statistics for experimental data.
        
        Args:
            data: List of ExperimentalData objects
            
        Returns:
            Dictionary with summary statistics
        """
        if not data:
            return {}
        
        doses = [exp.dose for exp in data]
        dose_rates = [exp.dose_rate for exp in data]
        exposure_times = [exp.exposure_time for exp in data]
        distances = [exp.distance for exp in data]
        
        materials = [exp.material for exp in data]
        source_types = [exp.source_type for exp in data]
        
        summary = {
            'total_records': len(data),
            'dose_statistics': {
                'mean': np.mean(doses),
                'std': np.std(doses),
                'min': np.min(doses),
                'max': np.max(doses),
                'median': np.median(doses)
            },
            'dose_rate_statistics': {
                'mean': np.mean(dose_rates),
                'std': np.std(dose_rates),
                'min': np.min(dose_rates),
                'max': np.max(dose_rates),
                'median': np.median(dose_rates)
            },
            'exposure_time_statistics': {
                'mean': np.mean(exposure_times),
                'std': np.std(exposure_times),
                'min': np.min(exposure_times),
                'max': np.max(exposure_times),
                'median': np.median(exposure_times)
            },
            'distance_statistics': {
                'mean': np.mean(distances),
                'std': np.std(distances),
                'min': np.min(distances),
                'max': np.max(distances),
                'median': np.median(distances)
            },
            'material_distribution': pd.Series(materials).value_counts().to_dict(),
            'source_type_distribution': pd.Series(source_types).value_counts().to_dict()
        }
        
        return summary