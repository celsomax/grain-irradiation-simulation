/**
 * Experimental data structure
 */
export interface ExperimentalData {
  sampleId: string;
  material: string;
  dose: number;
  doseRate?: number;
  exposureTime: number;
  sourceType: string;
  sourceActivity: number;
  distance: number;
  temperature?: number;
  humidity?: number;
  notes?: string;
}

/**
 * Data validation result
 */
export interface DataValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  validRecords: number;
  totalRecords: number;
  validationRate: number;
}

/**
 * Summary statistics for experimental data
 */
export interface DataSummary {
  totalRecords: number;
  doseStatistics: {
    mean: number;
    std: number;
    min: number;
    max: number;
    median: number;
  };
  materials: string[];
  sourceTypes: string[];
  materialCounts: Record<string, number>;
  sourceTypeCounts: Record<string, number>;
}

/**
 * Data loader and validation class
 */
export class DataLoader {
  private logger: Console;

  constructor() {
    this.logger = console;
  }

  /**
   * Load data from various formats
   */
  async loadData(input: string | File | ExperimentalData[]): Promise<ExperimentalData[]> {
    if (Array.isArray(input)) {
      this.logger.info(`Loaded ${input.length} experimental records from array`);
      return input;
    }

    if (typeof input === 'string') {
      // Try to parse as JSON
      try {
        const data = JSON.parse(input);
        return this.parseJsonData(data);
      } catch {
        // Try to parse as CSV
        return this.parseCsvData(input);
      }
    }

    if (input instanceof File) {
      return this.loadFromFile(input);
    }

    throw new Error('Unsupported input format');
  }

  /**
   * Load data from file
   */
  async loadFromFile(file: File): Promise<ExperimentalData[]> {
    const text = await file.text();
    const extension = file.name.toLowerCase().split('.').pop();

    switch (extension) {
      case 'json':
        return this.parseJsonData(JSON.parse(text));
      case 'csv':
        return this.parseCsvData(text);
      default:
        throw new Error(`Unsupported file format: ${extension}`);
    }
  }

  /**
   * Parse JSON data
   */
  private parseJsonData(data: any): ExperimentalData[] {
    let experiments: any[];

    if (Array.isArray(data)) {
      experiments = data;
    } else if (data.experiments && Array.isArray(data.experiments)) {
      experiments = data.experiments;
    } else {
      throw new Error('Invalid JSON format: expected array or object with experiments property');
    }

    const result = experiments.map((exp, index) => this.parseExperimentalRecord(exp, index));
    this.logger.info(`Loaded ${result.length} experimental records from JSON`);
    return result;
  }

  /**
   * Parse CSV data
   */
  private parseCsvData(csvText: string): ExperimentalData[] {
    const lines = csvText.trim().split('\n');
    if (lines.length < 2) {
      throw new Error('CSV must have at least a header and one data row');
    }

    const headers = lines[0].split(',').map(h => h.trim());
    const result: ExperimentalData[] = [];

    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim());
      const record: any = {};

      headers.forEach((header, index) => {
        if (values[index] !== undefined) {
          record[header] = values[index];
        }
      });

      try {
        const experimentalData = this.parseExperimentalRecord(record, i - 1);
        result.push(experimentalData);
      } catch (error) {
        this.logger.warn(`Error parsing CSV row ${i}:`, error);
      }
    }

    this.logger.info(`Loaded ${result.length} experimental records from CSV`);
    return result;
  }

  /**
   * Parse individual experimental record
   */
  private parseExperimentalRecord(record: any, _index: number): ExperimentalData {
    // Map possible field names to standard format
    const fieldMap: Record<string, string> = {
      'sample_id': 'sampleId',
      'sampleId': 'sampleId',
      'id': 'sampleId',
      'material': 'material',
      'dose': 'dose',
      'dose_rate': 'doseRate',
      'doseRate': 'doseRate',
      'exposure_time': 'exposureTime',
      'exposureTime': 'exposureTime',
      'time': 'exposureTime',
      'source_type': 'sourceType',
      'sourceType': 'sourceType',
      'source': 'sourceType',
      'source_activity': 'sourceActivity',
      'sourceActivity': 'sourceActivity',
      'activity': 'sourceActivity',
      'distance': 'distance',
      'temperature': 'temperature',
      'temp': 'temperature',
      'humidity': 'humidity',
      'notes': 'notes'
    };

    const normalized: any = {};

    // Normalize field names and convert types
    Object.keys(record).forEach(key => {
      const normalizedKey = fieldMap[key] || key;
      let value = record[key];

      // Convert numeric fields
      if (['dose', 'doseRate', 'exposureTime', 'sourceActivity', 'distance', 'temperature', 'humidity'].includes(normalizedKey)) {
        value = typeof value === 'string' ? parseFloat(value) : value;
        if (isNaN(value)) {
          throw new Error(`Invalid numeric value for ${normalizedKey}: ${record[key]}`);
        }
      }

      normalized[normalizedKey] = value;
    });

    // Validate required fields
    const required = ['sampleId', 'material', 'dose', 'exposureTime', 'sourceType', 'sourceActivity', 'distance'];
    for (const field of required) {
      if (normalized[field] === undefined || normalized[field] === null || normalized[field] === '') {
        throw new Error(`Missing required field: ${field}`);
      }
    }

    return {
      sampleId: String(normalized.sampleId),
      material: String(normalized.material).toLowerCase(),
      dose: normalized.dose,
      doseRate: normalized.doseRate,
      exposureTime: normalized.exposureTime,
      sourceType: String(normalized.sourceType),
      sourceActivity: normalized.sourceActivity,
      distance: normalized.distance,
      temperature: normalized.temperature,
      humidity: normalized.humidity,
      notes: normalized.notes ? String(normalized.notes) : undefined
    };
  }

  /**
   * Validate experimental data
   */
  validateData(data: ExperimentalData[]): DataValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    let validCount = 0;

    for (let i = 0; i < data.length; i++) {
      const experiment = data[i];
      const recordErrors: string[] = [];
      const recordWarnings: string[] = [];

      try {
        // Dose validation
        if (experiment.dose <= 0) {
          recordErrors.push(`Invalid dose: ${experiment.dose} Gy`);
        }
        if (experiment.dose > 100) {
          recordWarnings.push(`Very high dose: ${experiment.dose} Gy`);
        }

        // Exposure time validation
        if (experiment.exposureTime <= 0) {
          recordErrors.push(`Invalid exposure time: ${experiment.exposureTime} hours`);
        }
        if (experiment.exposureTime > 24) {
          recordWarnings.push(`Very long exposure time: ${experiment.exposureTime} hours`);
        }

        // Source activity validation
        if (experiment.sourceActivity <= 0) {
          recordErrors.push(`Invalid source activity: ${experiment.sourceActivity}`);
        }

        // Distance validation
        if (experiment.distance <= 0) {
          recordErrors.push(`Invalid distance: ${experiment.distance} cm`);
        }

        // Material validation
        const validMaterials = ['wheat', 'rice', 'corn', 'water'];
        if (!validMaterials.includes(experiment.material)) {
          recordWarnings.push(`Unknown material: ${experiment.material}`);
        }

        // Source type validation
        const validSources = ['Co-60', 'Cs-137', 'LinAc', 'Cobalt-60', 'Cesium-137', 'Linear Accelerator'];
        if (!validSources.includes(experiment.sourceType)) {
          recordWarnings.push(`Unknown source type: ${experiment.sourceType}`);
        }

        // Temperature validation
        if (experiment.temperature !== undefined) {
          if (experiment.temperature < -50 || experiment.temperature > 100) {
            recordWarnings.push(`Extreme temperature: ${experiment.temperature}°C`);
          }
        }

        // Humidity validation
        if (experiment.humidity !== undefined) {
          if (experiment.humidity < 0 || experiment.humidity > 100) {
            recordErrors.push(`Invalid humidity: ${experiment.humidity}%`);
          }
        }

        // Dose rate consistency check
        if (experiment.doseRate !== undefined) {
          const calculatedDoseRate = experiment.dose / experiment.exposureTime;
          const difference = Math.abs(experiment.doseRate - calculatedDoseRate) / calculatedDoseRate;
          if (difference > 0.1) { // 10% tolerance
            recordWarnings.push(`Dose rate inconsistent with dose and time`);
          }
        }

        if (recordErrors.length === 0) {
          validCount++;
        }

        // Add errors and warnings with record index
        if (recordErrors.length > 0) {
          errors.push(...recordErrors.map(err => `Record ${i + 1}: ${err}`));
        }
        if (recordWarnings.length > 0) {
          warnings.push(...recordWarnings.map(warn => `Record ${i + 1}: ${warn}`));
        }

      } catch (error) {
        errors.push(`Record ${i + 1}: Validation error - ${error}`);
      }
    }

    const result: DataValidationResult = {
      isValid: errors.length === 0,
      errors,
      warnings,
      validRecords: validCount,
      totalRecords: data.length,
      validationRate: data.length > 0 ? (validCount / data.length) * 100 : 0
    };

    this.logger.info(`Validation complete: ${result.validRecords}/${result.totalRecords} valid records (${result.validationRate.toFixed(1)}%)`);

    if (errors.length > 0) {
      this.logger.error(`Found ${errors.length} validation errors`);
    }
    if (warnings.length > 0) {
      this.logger.warn(`Found ${warnings.length} validation warnings`);
    }

    return result;
  }

  /**
   * Generate summary statistics
   */
  getSummaryStatistics(data: ExperimentalData[]): DataSummary {
    if (data.length === 0) {
      throw new Error('Cannot generate statistics for empty dataset');
    }

    const doses = data.map(d => d.dose).sort((a, b) => a - b);
    const materials = [...new Set(data.map(d => d.material))];
    const sourceTypes = [...new Set(data.map(d => d.sourceType))];

    const materialCounts: Record<string, number> = {};
    const sourceTypeCounts: Record<string, number> = {};

    data.forEach(d => {
      materialCounts[d.material] = (materialCounts[d.material] || 0) + 1;
      sourceTypeCounts[d.sourceType] = (sourceTypeCounts[d.sourceType] || 0) + 1;
    });

    const mean = doses.reduce((a, b) => a + b, 0) / doses.length;
    const variance = doses.reduce((sum, dose) => sum + Math.pow(dose - mean, 2), 0) / doses.length;
    const std = Math.sqrt(variance);
    const median = doses.length % 2 === 0 
      ? (doses[doses.length / 2 - 1] + doses[doses.length / 2]) / 2
      : doses[Math.floor(doses.length / 2)];

    return {
      totalRecords: data.length,
      doseStatistics: {
        mean,
        std,
        min: Math.min(...doses),
        max: Math.max(...doses),
        median
      },
      materials,
      sourceTypes,
      materialCounts,
      sourceTypeCounts
    };
  }

  /**
   * Filter data by criteria
   */
  filterData(data: ExperimentalData[], criteria: {
    material?: string;
    sourceType?: string;
    minDose?: number;
    maxDose?: number;
    minExposureTime?: number;
    maxExposureTime?: number;
  }): ExperimentalData[] {
    return data.filter(experiment => {
      if (criteria.material && experiment.material !== criteria.material) return false;
      if (criteria.sourceType && experiment.sourceType !== criteria.sourceType) return false;
      if (criteria.minDose !== undefined && experiment.dose < criteria.minDose) return false;
      if (criteria.maxDose !== undefined && experiment.dose > criteria.maxDose) return false;
      if (criteria.minExposureTime !== undefined && experiment.exposureTime < criteria.minExposureTime) return false;
      if (criteria.maxExposureTime !== undefined && experiment.exposureTime > criteria.maxExposureTime) return false;
      return true;
    });
  }

  /**
   * Export data to different formats
   */
  exportData(data: ExperimentalData[], format: 'json' | 'csv'): string {
    switch (format) {
      case 'json':
        return JSON.stringify({ experiments: data }, null, 2);
      
      case 'csv': {
        if (data.length === 0) return '';
        
        const headers = [
          'sample_id', 'material', 'dose', 'dose_rate', 'exposure_time',
          'source_type', 'source_activity', 'distance', 'temperature', 'humidity', 'notes'
        ];
        
        const csvLines = [headers.join(',')];
        
        data.forEach(exp => {
          const row = [
            exp.sampleId,
            exp.material,
            exp.dose,
            exp.doseRate || '',
            exp.exposureTime,
            exp.sourceType,
            exp.sourceActivity,
            exp.distance,
            exp.temperature || '',
            exp.humidity || '',
            exp.notes || ''
          ];
          csvLines.push(row.join(','));
        });
        
        return csvLines.join('\n');
      }
      
      default:
        throw new Error(`Unsupported export format: ${format}`);
    }
  }

  /**
   * Create sample experimental data for testing
   */
  createSampleData(): ExperimentalData[] {
    return [
      {
        sampleId: 'WH001',
        material: 'wheat',
        dose: 2.5,
        doseRate: 1.25,
        exposureTime: 2.0,
        sourceType: 'Co-60',
        sourceActivity: 1000,
        distance: 50,
        temperature: 25,
        humidity: 65,
        notes: 'Sample wheat irradiation'
      },
      {
        sampleId: 'RC001',
        material: 'rice',
        dose: 3.0,
        doseRate: 1.5,
        exposureTime: 2.0,
        sourceType: 'Cs-137',
        sourceActivity: 800,
        distance: 60,
        temperature: 20,
        humidity: 70,
        notes: 'Sample rice irradiation'
      },
      {
        sampleId: 'CR001',
        material: 'corn',
        dose: 4.5,
        doseRate: 2.25,
        exposureTime: 2.0,
        sourceType: 'LinAc',
        sourceActivity: 1200,
        distance: 40,
        temperature: 22,
        humidity: 60,
        notes: 'Sample corn irradiation'
      }
    ];
  }
}