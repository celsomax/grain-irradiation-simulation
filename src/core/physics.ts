/**
 * Radiation source types supported by the simulation
 */
export enum RadiationSource {
  COBALT_60 = 'Co-60',
  LINEAR_ACCELERATOR = 'LinAc',
  CESIUM_137 = 'Cs-137'
}

/**
 * Physical properties of materials being irradiated
 */
export interface MaterialProperties {
  /** Density in g/cm³ */
  density: number;
  /** Effective atomic number */
  atomicNumber: number;
  /** Mass attenuation coefficient in cm²/g */
  massAttenuationCoefficient: number;
  /** Material name */
  name: string;
}

/**
 * Sample geometry configuration
 */
export interface GeometryConfig {
  /** Geometry shape: "sphere", "cylinder", or "box" */
  shape: 'sphere' | 'cylinder' | 'box';
  /** Geometry-specific dimensions */
  dimensions: Record<string, number>;
  /** Volume in cm³ (calculated if not provided) */
  volume?: number;
}

/**
 * Core physics engine for irradiation calculations
 */
export class IrradiationPhysics {
  private readonly standardMaterials: Record<string, MaterialProperties>;
  private readonly sourceProperties: Record<RadiationSource, any>;

  constructor() {
    // Initialize standard material properties
    this.standardMaterials = {
      wheat: {
        density: 0.8,
        atomicNumber: 6.5,
        massAttenuationCoefficient: 0.0302,
        name: 'wheat'
      },
      rice: {
        density: 0.75,
        atomicNumber: 6.3,
        massAttenuationCoefficient: 0.0298,
        name: 'rice'
      },
      corn: {
        density: 0.85,
        atomicNumber: 6.7,
        massAttenuationCoefficient: 0.0305,
        name: 'corn'
      },
      water: {
        density: 1.0,
        atomicNumber: 7.4,
        massAttenuationCoefficient: 0.0270,
        name: 'water'
      }
    };

    // Initialize radiation source properties
    this.sourceProperties = {
      [RadiationSource.COBALT_60]: {
        energy: 1.25, // MeV (average of 1.17 and 1.33 MeV)
        halfLife: 5.27, // years
        doseRateConstant: 1.32 // R·m²/(h·Ci)
      },
      [RadiationSource.CESIUM_137]: {
        energy: 0.662, // MeV
        halfLife: 30.1, // years
        doseRateConstant: 0.325 // R·m²/(h·Ci)
      },
      [RadiationSource.LINEAR_ACCELERATOR]: {
        energy: 10.0, // MeV (configurable)
        pulseFrequency: 300, // Hz
        beamCurrent: 10 // mA
      }
    };
  }

  /**
   * Get standard material properties
   */
  getStandardMaterials(): Record<string, MaterialProperties> {
    return { ...this.standardMaterials };
  }

  /**
   * Get radiation source properties
   */
  getSourceProperties(): Record<RadiationSource, any> {
    return { ...this.sourceProperties };
  }

  /**
   * Calculate dose rate at a given distance from source
   */
  calculateDoseRate(
    source: RadiationSource,
    activity: number,
    distance: number
  ): number {
    const properties = this.sourceProperties[source];
    
    if (!properties) {
      throw new Error(`Unknown radiation source: ${source}`);
    }

    let doseRate: number;

    if (source === RadiationSource.COBALT_60 || source === RadiationSource.CESIUM_137) {
      // For gamma sources: inverse square law
      const doseConstant = properties.doseRateConstant;
      doseRate = (doseConstant * activity * 0.00877) / (distance ** 2);
    } else {
      // For electron beams (simplified model)
      const beamPower = activity; // Assuming activity represents beam power in kW
      doseRate = (beamPower * 1000) / (4 * Math.PI * distance ** 2); // Simplified
    }

    console.info(`Calculated dose rate: ${doseRate.toFixed(4)} Gy/h at ${distance.toFixed(2)} m`);
    return doseRate;
  }

  /**
   * Calculate radiation attenuation through material
   */
  calculateAttenuation(
    material: MaterialProperties,
    thickness: number,
    _energy: number
  ): number {
    // Beer-Lambert law: I = I₀ * exp(-μ * ρ * x)
    const linearAttenuationCoeff = material.massAttenuationCoefficient * material.density;
    const transmission = Math.exp(-linearAttenuationCoeff * thickness);
    
    console.info(`Attenuation through ${thickness.toFixed(2)} cm of ${material.name}: ${transmission.toFixed(4)}`);
    return transmission;
  }

  /**
   * Calculate uniform dose for simple geometry
   */
  calculateUniformDose(
    material: MaterialProperties,
    source: RadiationSource,
    activity: number,
    distance: number,
    exposureTime: number
  ): number {
    const doseRate = this.calculateDoseRate(source, activity, distance);
    const properties = this.sourceProperties[source];
    const transmission = this.calculateAttenuation(material, 1.0, properties.energy);
    
    return doseRate * transmission * exposureTime;
  }

  /**
   * Calculate 2D dose distribution within geometry
   */
  calculateDoseDistribution(
    geometry: GeometryConfig,
    material: MaterialProperties,
    source: RadiationSource,
    sourceDistance: number,
    activity: number,
    exposureTime: number,
    gridPoints: number = 50
  ): { x: number[], y: number[], doseMatrix: number[][] } {
    const properties = this.sourceProperties[source];
    const energy = properties.energy;

    // Create coordinate grids
    const maxDimension = this.getMaxDimension(geometry);
    const range = maxDimension * 1.2; // Add some padding
    const step = (2 * range) / gridPoints;
    
    const x: number[] = [];
    const y: number[] = [];
    const doseMatrix: number[][] = [];

    for (let i = 0; i < gridPoints; i++) {
      x.push(-range + i * step);
      doseMatrix.push([]);
      for (let j = 0; j < gridPoints; j++) {
        if (i === 0) y.push(-range + j * step);
        
        const xi = x[i];
        const yj = y[j];

        if (this.pointInsideGeometry(xi, yj, geometry)) {
          // Calculate distance from source to point
          const distanceToPoint = Math.sqrt((xi - sourceDistance) ** 2 + yj ** 2);
          
          // Calculate dose rate at point
          const doseRate = this.calculateDoseRate(source, activity, distanceToPoint / 100); // Convert cm to m
          
          // Calculate path length through material to this point
          const pathLength = this.calculatePathLength(xi, yj, geometry);
          
          // Calculate attenuation
          const transmission = this.calculateAttenuation(material, pathLength, energy);
          
          // Final dose
          doseMatrix[i][j] = doseRate * transmission * exposureTime;
        } else {
          doseMatrix[i][j] = 0;
        }
      }
    }

    const maxDose = Math.max(...doseMatrix.flat());
    console.info(`Calculated dose distribution with max dose: ${maxDose.toFixed(2)} Gy`);

    return { x, y, doseMatrix };
  }

  /**
   * Get maximum dimension of geometry
   */
  private getMaxDimension(geometry: GeometryConfig): number {
    switch (geometry.shape) {
      case 'sphere':
        return geometry.dimensions.radius || 1.0;
      case 'cylinder':
        return Math.max(geometry.dimensions.radius || 1.0, geometry.dimensions.height || 1.0);
      case 'box':
        return Math.max(
          geometry.dimensions.length || 1.0,
          geometry.dimensions.width || 1.0,
          geometry.dimensions.height || 1.0
        );
      default:
        return 1.0;
    }
  }

  /**
   * Check if a point is inside the given geometry
   */
  private pointInsideGeometry(x: number, y: number, geometry: GeometryConfig): boolean {
    switch (geometry.shape) {
      case 'sphere': {
        const radius = geometry.dimensions.radius || 1.0;
        return (x ** 2 + y ** 2) <= radius ** 2;
      }
      case 'cylinder': {
        const radius = geometry.dimensions.radius || 1.0;
        const height = geometry.dimensions.height || 1.0;
        return (x ** 2 + y ** 2) <= radius ** 2 && Math.abs(y) <= height / 2;
      }
      case 'box': {
        const length = geometry.dimensions.length || 1.0;
        const width = geometry.dimensions.width || 1.0;
        return Math.abs(x) <= length / 2 && Math.abs(y) <= width / 2;
      }
      default:
        return false;
    }
  }

  /**
   * Calculate path length from surface to point inside geometry
   */
  private calculatePathLength(x: number, y: number, geometry: GeometryConfig): number {
    // Simplified calculation - assumes radiation enters from one side
    switch (geometry.shape) {
      case 'sphere': {
        const radius = geometry.dimensions.radius || 1.0;
        const distanceFromCenter = Math.sqrt(x ** 2 + y ** 2);
        return radius - distanceFromCenter;
      }
      case 'cylinder': {
        const radius = geometry.dimensions.radius || 1.0;
        const distanceFromAxis = Math.sqrt(x ** 2);
        return radius - distanceFromAxis;
      }
      case 'box': {
        const length = geometry.dimensions.length || 1.0;
        return length / 2 - Math.abs(x);
      }
      default:
        return 1.0;
    }
  }

  /**
   * Calculate geometry volume
   */
  calculateVolume(geometry: GeometryConfig): number {
    switch (geometry.shape) {
      case 'sphere': {
        const radius = geometry.dimensions.radius || 1.0;
        return (4 / 3) * Math.PI * radius ** 3;
      }
      case 'cylinder': {
        const radius = geometry.dimensions.radius || 1.0;
        const height = geometry.dimensions.height || 1.0;
        return Math.PI * radius ** 2 * height;
      }
      case 'box': {
        const length = geometry.dimensions.length || 1.0;
        const width = geometry.dimensions.width || 1.0;
        const height = geometry.dimensions.height || 1.0;
        return length * width * height;
      }
      default:
        return 1.0;
    }
  }

  /**
   * Validate input parameters for physical reasonableness
   */
  validateParameters(params: {
    activity?: number;
    distance?: number;
    exposureTime?: number;
    material?: MaterialProperties;
  }): boolean {
    const checks = [
      !params.activity || params.activity > 0,
      !params.distance || params.distance > 0,
      !params.exposureTime || params.exposureTime > 0,
      !params.material || (params.material.density > 0 && params.material.atomicNumber > 0)
    ];

    return checks.every(check => check);
  }
}