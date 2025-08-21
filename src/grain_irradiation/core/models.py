"""
Mathematical models for grain irradiation effects.

This module implements specific models for microbial inactivation,
grain quality changes, and biochemical effects of irradiation.
"""

import numpy as np
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


class MicrobialType(Enum):
    """Types of microorganisms commonly found in grains."""
    BACTERIA = "bacteria"
    MOLD = "mold"
    YEAST = "yeast"
    INSECTS = "insects"


@dataclass
class MicrobialInactivationResult:
    """Results of microbial inactivation calculation."""
    initial_population: float  # log CFU/g
    final_population: float    # log CFU/g
    log_reduction: float       # log cycles
    survival_fraction: float   # fraction surviving
    d_value: float            # D-value (Gy) for 1 log reduction


@dataclass
class GrainQualityResult:
    """Results of grain quality assessment."""
    germination_rate: float      # % (0-100)
    protein_retention: float     # % of original
    starch_damage: float         # % damage
    vitamin_retention: float     # % of original
    sensory_score: float        # 0-10 scale
    overall_quality: float      # 0-100 scale


class GrainIrradiationModels:
    """
    Mathematical models for grain irradiation effects.
    
    This class implements validated models for:
    - Microbial inactivation kinetics
    - Grain quality changes
    - Biochemical alterations
    - Nutritional impacts
    """
    
    def __init__(self):
        """Initialize the models with default parameters."""
        self.logger = logging.getLogger(__name__ + ".GrainIrradiationModels")
        
        # D-values (dose for 1 log reduction) for different microorganisms in grains
        # Values in Gy, based on literature data
        self.d_values = {
            MicrobialType.BACTERIA: {
                'default': 0.25,
                'salmonella': 0.4,
                'e_coli': 0.3,
                'bacillus': 1.5  # spore-forming
            },
            MicrobialType.MOLD: {
                'default': 0.4,
                'aspergillus': 0.6,
                'penicillium': 0.5,
                'fusarium': 0.7
            },
            MicrobialType.YEAST: {
                'default': 1.2,
                'candida': 1.0,
                'saccharomyces': 1.5
            },
            MicrobialType.INSECTS: {
                'default': 50,
                'weevil_adult': 60,
                'weevil_larvae': 40,
                'moth_larvae': 45
            }
        }
        
        # Quality degradation parameters
        self.quality_parameters = {
            'wheat': {
                'germination_d90': 8.0,    # Dose for 90% germination loss
                'protein_slope': -0.002,    # %/Gy protein loss
                'starch_threshold': 5.0,    # Gy threshold for starch damage
                'vitamin_slope': -0.05,     # %/Gy vitamin loss
                'max_recommended_dose': 1.0  # Gy
            },
            'rice': {
                'germination_d90': 6.0,
                'protein_slope': -0.003,
                'starch_threshold': 4.0,
                'vitamin_slope': -0.04,
                'max_recommended_dose': 1.5
            },
            'corn': {
                'germination_d90': 10.0,
                'protein_slope': -0.0015,
                'starch_threshold': 6.0,
                'vitamin_slope': -0.03,
                'max_recommended_dose': 1.0
            }
        }
    
    def calculate_microbial_inactivation(self, 
                                       dose: float,
                                       microbial_type: MicrobialType,
                                       initial_population: float = 6.0,
                                       specific_organism: Optional[str] = None) -> MicrobialInactivationResult:
        """
        Calculate microbial inactivation using linear dose-response model.
        
        Args:
            dose: Radiation dose (Gy)
            microbial_type: Type of microorganism
            initial_population: Initial population (log CFU/g)
            specific_organism: Specific organism name for precise D-value
            
        Returns:
            MicrobialInactivationResult with inactivation details
        """
        # Get D-value
        if specific_organism and specific_organism in self.d_values[microbial_type]:
            d_value = self.d_values[microbial_type][specific_organism]
        else:
            d_value = self.d_values[microbial_type]['default']
        
        # Calculate log reduction (first-order kinetics)
        log_reduction = dose / d_value
        
        # Calculate final population
        final_population = max(0, initial_population - log_reduction)
        
        # Calculate survival fraction
        survival_fraction = 10 ** (-log_reduction)
        
        result = MicrobialInactivationResult(
            initial_population=initial_population,
            final_population=final_population,
            log_reduction=log_reduction,
            survival_fraction=survival_fraction,
            d_value=d_value
        )
        
        self.logger.debug(f"Microbial inactivation: {log_reduction:.2f} log reduction "
                         f"for {microbial_type.value} at {dose:.2f} Gy")
        
        return result
    
    def calculate_grain_quality_effects(self, 
                                      dose: float,
                                      grain_type: str,
                                      temperature: Optional[float] = None,
                                      moisture_content: Optional[float] = None) -> GrainQualityResult:
        """
        Calculate effects of irradiation on grain quality parameters.
        
        Args:
            dose: Radiation dose (Gy)
            grain_type: Type of grain (wheat, rice, corn)
            temperature: Storage temperature (°C)
            moisture_content: Moisture content (%)
            
        Returns:
            GrainQualityResult with quality parameters
        """
        if grain_type not in self.quality_parameters:
            grain_type = 'wheat'  # Default
        
        params = self.quality_parameters[grain_type]
        
        # Germination rate (exponential decay)
        germination_rate = 100 * np.exp(-dose / params['germination_d90'] * np.log(10))
        germination_rate = max(0, min(100, germination_rate))
        
        # Protein retention (linear degradation)
        protein_retention = 100 + params['protein_slope'] * dose * 100
        protein_retention = max(70, min(100, protein_retention))  # 70-100% range
        
        # Starch damage (threshold effect)
        if dose < params['starch_threshold']:
            starch_damage = 0.1 * dose  # Minimal damage below threshold
        else:
            starch_damage = 0.1 * params['starch_threshold'] + 2 * (dose - params['starch_threshold'])
        starch_damage = max(0, min(30, starch_damage))  # 0-30% range
        
        # Vitamin retention (linear degradation)
        vitamin_retention = 100 + params['vitamin_slope'] * dose * 100
        vitamin_retention = max(50, min(100, vitamin_retention))  # 50-100% range
        
        # Temperature and moisture effects (if provided)
        if temperature is not None and temperature > 25:
            # Higher temperature increases degradation
            temp_factor = 1 + (temperature - 25) * 0.01
            protein_retention /= temp_factor
            vitamin_retention /= temp_factor
        
        if moisture_content is not None and moisture_content > 14:
            # Higher moisture increases degradation
            moisture_factor = 1 + (moisture_content - 14) * 0.005
            germination_rate /= moisture_factor
            protein_retention /= moisture_factor
        
        # Sensory score (empirical model)
        if dose <= params['max_recommended_dose']:
            sensory_score = 10 - dose * 0.5  # Minimal impact
        else:
            excess_dose = dose - params['max_recommended_dose']
            sensory_score = 10 - params['max_recommended_dose'] * 0.5 - excess_dose * 2
        sensory_score = max(3, min(10, sensory_score))  # 3-10 range
        
        # Overall quality (weighted average)
        overall_quality = (
            germination_rate * 0.3 +
            protein_retention * 0.25 +
            (100 - starch_damage) * 0.2 +
            vitamin_retention * 0.15 +
            sensory_score * 10 * 0.1  # Convert to 0-100 scale
        )
        
        result = GrainQualityResult(
            germination_rate=germination_rate,
            protein_retention=protein_retention,
            starch_damage=starch_damage,
            vitamin_retention=vitamin_retention,
            sensory_score=sensory_score,
            overall_quality=overall_quality
        )
        
        self.logger.debug(f"Quality assessment for {grain_type} at {dose:.2f} Gy: "
                         f"overall quality {overall_quality:.1f}%")
        
        return result
    
    def calculate_biochemical_changes(self, 
                                    dose: float,
                                    grain_type: str) -> Dict[str, Any]:
        """
        Calculate biochemical changes in grain components.
        
        Args:
            dose: Radiation dose (Gy)
            grain_type: Type of grain
            
        Returns:
            Dictionary with biochemical change indicators
        """
        # Lipid peroxidation (increases with dose)
        lipid_peroxidation = dose * 0.1 + dose**2 * 0.005  # Non-linear increase
        
        # Antioxidant activity (decreases with dose)
        antioxidant_retention = 100 * np.exp(-dose * 0.15)
        
        # Amino acid changes (minimal below 2 Gy)
        if dose < 2.0:
            amino_acid_loss = dose * 0.5
        else:
            amino_acid_loss = 1.0 + (dose - 2.0) * 2.0
        
        # Fatty acid changes
        fatty_acid_degradation = dose * 0.8 if dose > 1.0 else 0
        
        # Enzyme activity changes
        enzyme_activity = 100 * np.exp(-dose * 0.25)
        
        # Starch molecular changes
        starch_molecular_weight_change = dose * 1.5 if dose > 3.0 else 0
        
        # Free radical formation (temporary, peaks then decays)
        free_radical_formation = dose * 10 * np.exp(-dose * 0.1)
        
        return {
            'lipid_peroxidation_index': lipid_peroxidation,
            'antioxidant_retention_percent': antioxidant_retention,
            'amino_acid_loss_percent': amino_acid_loss,
            'fatty_acid_degradation_percent': fatty_acid_degradation,
            'enzyme_activity_percent': enzyme_activity,
            'starch_molecular_weight_change_percent': starch_molecular_weight_change,
            'free_radical_formation_index': free_radical_formation
        }
    
    def get_treatment_recommendation(self, 
                                   grain_type: str,
                                   target_log_reduction: float,
                                   microbial_type: MicrobialType = MicrobialType.BACTERIA) -> Dict[str, Any]:
        """
        Get treatment recommendation for specific grain and target microbial reduction.
        
        Args:
            grain_type: Type of grain
            target_log_reduction: Desired log reduction in microbial population
            microbial_type: Target microorganism type
            
        Returns:
            Dictionary with treatment recommendations
        """
        # Calculate required dose
        d_value = self.d_values[microbial_type]['default']
        required_dose = target_log_reduction * d_value
        
        # Get quality effects at this dose
        quality_result = self.calculate_grain_quality_effects(required_dose, grain_type)
        
        # Check if dose is within recommended limits
        max_recommended = self.quality_parameters.get(grain_type, {}).get('max_recommended_dose', 1.0)
        within_limits = required_dose <= max_recommended
        
        # Generate recommendation
        if within_limits:
            recommendation = f"Recommended dose: {required_dose:.2f} Gy"
            safety_level = "Safe"
        elif required_dose <= max_recommended * 2:
            recommendation = f"Acceptable dose: {required_dose:.2f} Gy (monitor quality)"
            safety_level = "Caution"
        else:
            recommendation = f"High dose: {required_dose:.2f} Gy (significant quality impact expected)"
            safety_level = "High risk"
        
        return {
            'required_dose_Gy': required_dose,
            'target_log_reduction': target_log_reduction,
            'microbial_type': microbial_type.value,
            'grain_type': grain_type,
            'recommendation': recommendation,
            'safety_level': safety_level,
            'within_recommended_limits': within_limits,
            'expected_quality': quality_result.__dict__,
            'max_recommended_dose_Gy': max_recommended
        }
    
    def validate_treatment_parameters(self, 
                                    dose: float,
                                    grain_type: str,
                                    target_use: str = "food") -> Dict[str, Any]:
        """
        Validate treatment parameters against standards and recommendations.
        
        Args:
            dose: Proposed radiation dose (Gy)
            grain_type: Type of grain
            target_use: Intended use ("food", "seed", "feed")
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'regulatory_status': 'Unknown'
        }
        
        # Regulatory limits (simplified, varies by country)
        regulatory_limits = {
            'food': 1.0,    # Generally accepted limit for food grains
            'seed': 0.1,    # Lower limit to preserve germination
            'feed': 10.0    # Higher limit acceptable for animal feed
        }
        
        limit = regulatory_limits.get(target_use, 1.0)
        
        # Check regulatory compliance
        if dose > limit:
            validation_result['errors'].append(
                f"Dose {dose:.2f} Gy exceeds regulatory limit {limit:.2f} Gy for {target_use}"
            )
            validation_result['is_valid'] = False
            validation_result['regulatory_status'] = 'Non-compliant'
        else:
            validation_result['regulatory_status'] = 'Compliant'
        
        # Quality warnings
        quality_result = self.calculate_grain_quality_effects(dose, grain_type)
        
        if quality_result.germination_rate < 80 and target_use == 'seed':
            validation_result['warnings'].append(
                f"Low germination rate ({quality_result.germination_rate:.1f}%) for seed use"
            )
        
        if quality_result.overall_quality < 70:
            validation_result['warnings'].append(
                f"Overall quality below 70% ({quality_result.overall_quality:.1f}%)"
            )
        
        if quality_result.sensory_score < 6:
            validation_result['warnings'].append(
                f"Low sensory score ({quality_result.sensory_score:.1f}/10)"
            )
        
        return validation_result