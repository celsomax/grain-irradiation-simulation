import { IrradiationPhysics, RadiationSource, MaterialProperties, GeometryConfig } from './physics.js';
import { ExperimentalData } from '../data/loader.js';

/**
 * Configuration parameters for irradiation simulation
 */
export interface SimulationParameters {
  source: RadiationSource;
  sourceActivity: number; // Ci or kW
  sourceDistance: number; // cm
  exposureTime: number; // hours
  material: MaterialProperties;
  geometry: GeometryConfig;
  temperature?: number; // °C
  humidity?: number; // %
  gridResolution: number;
}

/**
 * Container for simulation results
 */
export interface SimulationResults {
  parameters: SimulationParameters;
  uniformDose: number; // Gy
  maxDose: number; // Gy
  minDose: number; // Gy
  meanDose: number; // Gy
  doseUniformity: number; // min/max ratio
  doseDistribution?: number[][];
  coordinates?: { x: number[], y: number[] };
  computationTime: number;
  timestamp: string;
}

/**
 * Results of experimental vs simulation comparison
 */
export interface ComparisonResults {
  experimentalData: ExperimentalData[];
  simulationResults: SimulationResults[];
  correlationCoefficient: number;
  meanAbsoluteError: number; // Gy
  relativeError: number; // %
  statistics: Record<string, any>;
}

/**
 * Main simulation engine for grain irradiation processes
 */
export class IrradiationSimulator {
  private readonly physics: IrradiationPhysics;
  private readonly defaultMaterials: Record<string, MaterialProperties>;

  constructor() {
    this.physics = new IrradiationPhysics();
    this.defaultMaterials = this.physics.getStandardMaterials();
  }

  /**
   * Create simulation parameters from input values
   */
  createSimulationParameters(config: {
    sourceType: string;
    materialName: string;
    sourceActivity: number;
    sourceDistance: number;
    exposureTime: number;
    geometryConfig: {
      shape: 'sphere' | 'cylinder' | 'box';
      dimensions: Record<string, number>;
    };
    temperature?: number;
    humidity?: number;
    gridResolution?: number;
  }): SimulationParameters {
    // Map source type string to enum
    const sourceMap: Record<string, RadiationSource> = {
      'Co-60': RadiationSource.COBALT_60,
      'Cobalt-60': RadiationSource.COBALT_60,
      'Cs-137': RadiationSource.CESIUM_137,
      'Cesium-137': RadiationSource.CESIUM_137,
      'LinAc': RadiationSource.LINEAR_ACCELERATOR,
      'Linear Accelerator': RadiationSource.LINEAR_ACCELERATOR
    };

    if (!(config.sourceType in sourceMap)) {
      throw new Error(`Unknown source type: ${config.sourceType}`);
    }

    const source = sourceMap[config.sourceType];

    // Get material properties
    if (!(config.materialName in this.defaultMaterials)) {
      throw new Error(`Unknown material: ${config.materialName}`);
    }

    const material = this.defaultMaterials[config.materialName];

    // Create geometry configuration
    const geometry: GeometryConfig = {
      shape: config.geometryConfig.shape,
      dimensions: config.geometryConfig.dimensions,
      volume: this.physics.calculateVolume(config.geometryConfig)
    };

    // Create parameters
    const params: SimulationParameters = {
      source,
      sourceActivity: config.sourceActivity,
      sourceDistance: config.sourceDistance,
      exposureTime: config.exposureTime,
      material,
      geometry,
      temperature: config.temperature,
      humidity: config.humidity,
      gridResolution: config.gridResolution || 50
    };

    if (!this.validateParameters(params)) {
      throw new Error('Invalid simulation parameters');
    }

    return params;
  }

  /**
   * Run a single simulation
   */
  async runSimulation(
    parameters: SimulationParameters,
    calculateDistribution: boolean = true
  ): Promise<SimulationResults> {
    const startTime = performance.now();

    console.info('Starting simulation...', parameters);

    // Calculate uniform dose
    const uniformDose = this.physics.calculateUniformDose(
      parameters.material,
      parameters.source,
      parameters.sourceActivity,
      parameters.sourceDistance / 100, // Convert cm to m
      parameters.exposureTime
    );

    let doseDistribution: number[][] | undefined;
    let coordinates: { x: number[], y: number[] } | undefined;
    let maxDose = uniformDose;
    let minDose = uniformDose;
    let meanDose = uniformDose;

    if (calculateDistribution) {
      const result = this.physics.calculateDoseDistribution(
        parameters.geometry,
        parameters.material,
        parameters.source,
        parameters.sourceDistance,
        parameters.sourceActivity,
        parameters.exposureTime,
        parameters.gridResolution
      );

      doseDistribution = result.doseMatrix;
      coordinates = { x: result.x, y: result.y };

      // Calculate statistics
      const flatDoses = doseDistribution.flat().filter(dose => dose > 0);
      if (flatDoses.length > 0) {
        maxDose = Math.max(...flatDoses);
        minDose = Math.min(...flatDoses);
        meanDose = flatDoses.reduce((sum, dose) => sum + dose, 0) / flatDoses.length;
      }
    }

    const doseUniformity = maxDose > 0 ? minDose / maxDose : 0;
    const computationTime = (performance.now() - startTime) / 1000; // Convert to seconds

    const results: SimulationResults = {
      parameters,
      uniformDose,
      maxDose,
      minDose,
      meanDose,
      doseUniformity,
      doseDistribution: calculateDistribution ? doseDistribution : undefined,
      coordinates: calculateDistribution ? coordinates : undefined,
      computationTime,
      timestamp: new Date().toISOString()
    };

    console.info(`Simulation completed in ${computationTime.toFixed(3)}s`);
    console.info(`Results: Mean dose = ${meanDose.toFixed(2)} Gy, Uniformity = ${doseUniformity.toFixed(3)}`);

    return results;
  }

  /**
   * Run multiple simulations in batch
   */
  async runBatchSimulation(parameterSets: SimulationParameters[]): Promise<SimulationResults[]> {
    console.info(`Starting batch simulation with ${parameterSets.length} parameter sets`);
    
    const results: SimulationResults[] = [];
    
    for (let i = 0; i < parameterSets.length; i++) {
      console.info(`Running simulation ${i + 1}/${parameterSets.length}`);
      const result = await this.runSimulation(parameterSets[i], false); // Skip distribution for batch
      results.push(result);
    }

    console.info('Batch simulation completed');
    return results;
  }

  /**
   * Compare simulation results with experimental data
   */
  async compareWithExperimental(
    experimentalData: ExperimentalData[],
    _simulationTolerance: number = 0.1
  ): Promise<ComparisonResults> {
    console.info(`Comparing with ${experimentalData.length} experimental data points`);

    const simulationResults: SimulationResults[] = [];

    // Run simulations for each experimental data point
    for (const experiment of experimentalData) {
      try {
        const params = this.createSimulationParameters({
          sourceType: experiment.sourceType,
          materialName: experiment.material,
          sourceActivity: experiment.sourceActivity,
          sourceDistance: experiment.distance,
          exposureTime: experiment.exposureTime,
          geometryConfig: {
            shape: 'sphere', // Default to sphere if not specified
            dimensions: { radius: 1.0 }
          },
          temperature: experiment.temperature,
          humidity: experiment.humidity
        });

        const result = await this.runSimulation(params, false);
        simulationResults.push(result);
      } catch (error) {
        console.warn(`Failed to simulate experiment ${experiment.sampleId}:`, error);
      }
    }

    // Calculate correlation and errors
    const experimentalDoses = experimentalData.map(exp => exp.dose);
    const simulatedDoses = simulationResults.map(sim => sim.uniformDose);

    const correlationCoefficient = this.calculateCorrelation(experimentalDoses, simulatedDoses);
    const meanAbsoluteError = this.calculateMAE(experimentalDoses, simulatedDoses);
    const relativeError = this.calculateRelativeError(experimentalDoses, simulatedDoses);

    const statistics = {
      experimentalMean: experimentalDoses.reduce((a, b) => a + b, 0) / experimentalDoses.length,
      simulatedMean: simulatedDoses.reduce((a, b) => a + b, 0) / simulatedDoses.length,
      experimentalStd: this.calculateStandardDeviation(experimentalDoses),
      simulatedStd: this.calculateStandardDeviation(simulatedDoses)
    };

    return {
      experimentalData,
      simulationResults,
      correlationCoefficient,
      meanAbsoluteError,
      relativeError,
      statistics
    };
  }

  /**
   * Optimize exposure parameters for target dose
   */
  async optimizeExposureParameters(config: {
    targetDose: number;
    materialName: string;
    sourceType: string;
    sourceActivity: number;
    sourceDistance: number;
    tolerance?: number;
    maxIterations?: number;
  }): Promise<SimulationParameters> {
    const tolerance = config.tolerance || 0.01; // 1% tolerance
    const maxIterations = config.maxIterations || 50;

    let exposureTime = 1.0; // Initial guess
    let iteration = 0;

    while (iteration < maxIterations) {
      const params = this.createSimulationParameters({
        sourceType: config.sourceType,
        materialName: config.materialName,
        sourceActivity: config.sourceActivity,
        sourceDistance: config.sourceDistance,
        exposureTime,
        geometryConfig: {
          shape: 'sphere',
          dimensions: { radius: 1.0 }
        }
      });

      const result = await this.runSimulation(params, false);
      const currentDose = result.uniformDose;
      const error = Math.abs(currentDose - config.targetDose) / config.targetDose;

      if (error < tolerance) {
        console.info(`Optimization converged after ${iteration + 1} iterations`);
        console.info(`Target dose: ${config.targetDose} Gy, Achieved: ${currentDose.toFixed(3)} Gy`);
        return params;
      }

      // Adjust exposure time
      exposureTime *= config.targetDose / currentDose;
      iteration++;
    }

    throw new Error(`Optimization failed to converge after ${maxIterations} iterations`);
  }

  /**
   * Get available materials
   */
  getAvailableMaterials(): Record<string, MaterialProperties> {
    return { ...this.defaultMaterials };
  }

  /**
   * Get available radiation sources
   */
  getAvailableSources(): RadiationSource[] {
    return Object.values(RadiationSource);
  }

  /**
   * Validate simulation parameters
   */
  private validateParameters(parameters: SimulationParameters): boolean {
    return this.physics.validateParameters({
      activity: parameters.sourceActivity,
      distance: parameters.sourceDistance,
      exposureTime: parameters.exposureTime,
      material: parameters.material
    }) && parameters.gridResolution > 0;
  }

  /**
   * Calculate Pearson correlation coefficient
   */
  private calculateCorrelation(x: number[], y: number[]): number {
    if (x.length !== y.length || x.length === 0) return 0;

    const meanX = x.reduce((a, b) => a + b, 0) / x.length;
    const meanY = y.reduce((a, b) => a + b, 0) / y.length;

    let numerator = 0;
    let denomX = 0;
    let denomY = 0;

    for (let i = 0; i < x.length; i++) {
      const deltaX = x[i] - meanX;
      const deltaY = y[i] - meanY;
      numerator += deltaX * deltaY;
      denomX += deltaX * deltaX;
      denomY += deltaY * deltaY;
    }

    const denominator = Math.sqrt(denomX * denomY);
    return denominator === 0 ? 0 : numerator / denominator;
  }

  /**
   * Calculate mean absolute error
   */
  private calculateMAE(experimental: number[], simulated: number[]): number {
    if (experimental.length !== simulated.length || experimental.length === 0) return 0;

    const errors = experimental.map((exp, i) => Math.abs(exp - simulated[i]));
    return errors.reduce((a, b) => a + b, 0) / errors.length;
  }

  /**
   * Calculate relative error
   */
  private calculateRelativeError(experimental: number[], simulated: number[]): number {
    if (experimental.length !== simulated.length || experimental.length === 0) return 0;

    const relativeErrors = experimental.map((exp, i) => 
      exp !== 0 ? Math.abs(exp - simulated[i]) / exp : 0
    );
    return (relativeErrors.reduce((a, b) => a + b, 0) / relativeErrors.length) * 100;
  }

  /**
   * Calculate standard deviation
   */
  private calculateStandardDeviation(values: number[]): number {
    if (values.length === 0) return 0;

    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const squaredDiffs = values.map(value => (value - mean) ** 2);
    const variance = squaredDiffs.reduce((a, b) => a + b, 0) / values.length;
    return Math.sqrt(variance);
  }
}