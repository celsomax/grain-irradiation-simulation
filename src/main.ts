import './ui/styles/main.css';
import { IrradiationSimulator, SimulationParameters, SimulationResults } from './core/simulator.js';
import { DataLoader, ExperimentalData } from './data/loader.js';
import { Visualizer } from './visualization/charts.js';
import { formatNumber, debounce, storage, EventEmitter } from './utils/helpers.js';

/**
 * Main application class
 */
class GrainIrradiationApp extends EventEmitter<{
  simulationComplete: SimulationResults;
  dataLoaded: ExperimentalData[];
  parameterChanged: any;
}> {
  private simulator: IrradiationSimulator;
  private dataLoader: DataLoader;
  private visualizer: Visualizer;
  private currentResults: SimulationResults | null = null;
  private currentData: ExperimentalData[] = [];

  constructor() {
    super();
    this.simulator = new IrradiationSimulator();
    this.dataLoader = new DataLoader();
    this.visualizer = new Visualizer();
    
    this.initializeApp();
  }

  /**
   * Initialize the application
   */
  private initializeApp(): void {
    this.setupEventListeners();
    this.loadStoredParameters();
    this.showToast('Welcome to Grain Irradiation Simulation!', 'info');
  }

  /**
   * Setup all event listeners
   */
  private setupEventListeners(): void {
    // Navigation
    const navBtns = document.querySelectorAll('.nav-btn');
    navBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const target = e.target as HTMLElement;
        const tabId = target.dataset.tab;
        if (tabId) {
          this.switchTab(tabId);
        }
      });
    });

    // Simulation controls
    document.getElementById('run-simulation')?.addEventListener('click', () => {
      this.runSimulation();
    });

    document.getElementById('optimize-parameters')?.addEventListener('click', () => {
      this.optimizeParameters();
    });

    document.getElementById('load-preset')?.addEventListener('click', () => {
      this.loadPreset();
    });

    // Data controls
    document.getElementById('data-file')?.addEventListener('change', (e) => {
      const target = e.target as HTMLInputElement;
      if (target.files?.[0]) {
        this.loadDataFile(target.files[0]);
      }
    });

    document.getElementById('load-sample-data')?.addEventListener('click', () => {
      this.loadSampleData();
    });

    document.getElementById('validate-data')?.addEventListener('click', () => {
      this.validateData();
    });

    document.getElementById('export-data')?.addEventListener('click', () => {
      this.exportData();
    });

    // Visualization controls
    document.getElementById('plot-dose-dist')?.addEventListener('click', () => {
      this.plotDoseDistribution();
    });

    document.getElementById('plot-comparison')?.addEventListener('click', () => {
      this.plotComparison();
    });

    document.getElementById('plot-3d')?.addEventListener('click', () => {
      this.plot3D();
    });

    document.getElementById('plot-statistics')?.addEventListener('click', () => {
      this.plotStatistics();
    });

    // Results controls
    document.getElementById('save-results')?.addEventListener('click', () => {
      this.saveResults();
    });

    document.getElementById('generate-report')?.addEventListener('click', () => {
      this.generateReport();
    });

    document.getElementById('export-images')?.addEventListener('click', () => {
      this.exportImages();
    });

    // Parameter change listeners
    const inputs = document.querySelectorAll('#simulation-tab input, #simulation-tab select');
    const debouncedSave = debounce(() => this.saveParameters(), 500);
    
    inputs.forEach(input => {
      input.addEventListener('change', () => {
        this.onParameterChange();
        debouncedSave();
      });
    });

    // Geometry type change
    document.getElementById('geometry')?.addEventListener('change', (e) => {
      const target = e.target as HTMLSelectElement;
      this.updateGeometryInputs(target.value as 'sphere' | 'cylinder' | 'box');
    });
  }

  /**
   * Switch between tabs
   */
  private switchTab(tabId: string): void {
    // Update navigation
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-tab="${tabId}"]`)?.classList.add('active');

    // Update content
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.getElementById(`${tabId}-tab`)?.classList.add('active');
  }

  /**
   * Run simulation with current parameters
   */
  private async runSimulation(): Promise<void> {
    try {
      this.showLoading(true);
      
      const parameters = this.getSimulationParameters();
      const results = await this.simulator.runSimulation(parameters, true);
      
      this.currentResults = results;
      this.updateQuickResults(results);
      this.updateLiveChart(results);
      
      this.emit('simulationComplete', results);
      this.showToast('Simulation completed successfully!', 'success');
      
    } catch (error) {
      console.error('Simulation error:', error);
      this.showToast(`Simulation failed: ${error}`, 'error');
    } finally {
      this.showLoading(false);
    }
  }

  /**
   * Get simulation parameters from UI
   */
  private getSimulationParameters(): SimulationParameters {
    const sourceType = (document.getElementById('source-type') as HTMLSelectElement).value;
    const material = (document.getElementById('material') as HTMLSelectElement).value;
    const activity = parseFloat((document.getElementById('activity') as HTMLInputElement).value);
    const distance = parseFloat((document.getElementById('distance') as HTMLInputElement).value);
    const exposureTime = parseFloat((document.getElementById('exposure-time') as HTMLInputElement).value);
    const geometry = (document.getElementById('geometry') as HTMLSelectElement).value as 'sphere' | 'cylinder' | 'box';
    
    // Get geometry dimensions
    let dimensions: Record<string, number> = {};
    
    switch (geometry) {
      case 'sphere':
        dimensions = {
          radius: parseFloat((document.getElementById('radius') as HTMLInputElement).value)
        };
        break;
      case 'cylinder':
        dimensions = {
          radius: parseFloat((document.getElementById('cyl-radius') as HTMLInputElement).value),
          height: parseFloat((document.getElementById('height') as HTMLInputElement).value)
        };
        break;
      case 'box':
        dimensions = {
          length: parseFloat((document.getElementById('length') as HTMLInputElement).value),
          width: parseFloat((document.getElementById('width') as HTMLInputElement).value),
          height: parseFloat((document.getElementById('box-height') as HTMLInputElement).value)
        };
        break;
    }

    // Get advanced options
    const temperature = (document.getElementById('temperature') as HTMLInputElement).value;
    const humidity = (document.getElementById('humidity') as HTMLInputElement).value;
    const gridResolution = parseInt((document.getElementById('grid-resolution') as HTMLInputElement).value);

    return this.simulator.createSimulationParameters({
      sourceType,
      materialName: material,
      sourceActivity: activity,
      sourceDistance: distance,
      exposureTime,
      geometryConfig: { shape: geometry, dimensions },
      temperature: temperature ? parseFloat(temperature) : undefined,
      humidity: humidity ? parseFloat(humidity) : undefined,
      gridResolution
    });
  }

  /**
   * Update geometry input fields based on selected geometry
   */
  private updateGeometryInputs(geometry: 'sphere' | 'cylinder' | 'box'): void {
    // Hide all geometry inputs
    document.querySelectorAll('.geometry-inputs').forEach(el => {
      el.classList.add('hidden');
    });

    // Show relevant inputs
    document.getElementById(`${geometry}-dimensions`)?.classList.remove('hidden');
  }

  /**
   * Update quick results display
   */
  private updateQuickResults(results: SimulationResults): void {
    document.getElementById('uniform-dose')!.textContent = `${formatNumber(results.uniformDose, 3)} Gy`;
    document.getElementById('mean-dose')!.textContent = `${formatNumber(results.meanDose, 3)} Gy`;
    document.getElementById('max-dose')!.textContent = `${formatNumber(results.maxDose, 3)} Gy`;
    document.getElementById('min-dose')!.textContent = `${formatNumber(results.minDose, 3)} Gy`;
    document.getElementById('dose-uniformity')!.textContent = formatNumber(results.doseUniformity, 3);
    document.getElementById('computation-time')!.textContent = `${formatNumber(results.computationTime, 3)} s`;
  }

  /**
   * Update live chart with simulation results
   */
  private updateLiveChart(results: SimulationResults): void {
    const canvas = document.getElementById('live-chart') as HTMLCanvasElement;
    if (canvas && results.doseDistribution) {
      this.visualizer.plotDoseDistribution2D(canvas, results, {
        title: 'Dose Distribution',
        showLegend: true
      });
    }
  }

  /**
   * Load data from file
   */
  private async loadDataFile(file: File): Promise<void> {
    try {
      this.showLoading(true);
      
      const data = await this.dataLoader.loadFromFile(file);
      this.currentData = data;
      this.updateDataTable(data);
      this.updateDataSummary(data);
      
      this.emit('dataLoaded', data);
      this.showToast(`Loaded ${data.length} experimental records`, 'success');
      
    } catch (error) {
      console.error('Data loading error:', error);
      this.showToast(`Failed to load data: ${error}`, 'error');
    } finally {
      this.showLoading(false);
    }
  }

  /**
   * Load sample data for demonstration
   */
  private loadSampleData(): void {
    const sampleData = this.dataLoader.createSampleData();
    this.currentData = sampleData;
    this.updateDataTable(sampleData);
    this.updateDataSummary(sampleData);
    
    this.emit('dataLoaded', sampleData);
    this.showToast(`Loaded ${sampleData.length} sample records`, 'info');
  }

  /**
   * Update data table display
   */
  private updateDataTable(data: ExperimentalData[]): void {
    const tbody = document.querySelector('#data-table tbody');
    if (!tbody) return;

    tbody.innerHTML = '';
    
    data.forEach(exp => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${exp.sampleId}</td>
        <td>${exp.material}</td>
        <td>${formatNumber(exp.dose, 2)}</td>
        <td>${exp.sourceType}</td>
        <td>${formatNumber(exp.sourceActivity, 0)}</td>
        <td>${formatNumber(exp.exposureTime, 1)}</td>
      `;
      tbody.appendChild(row);
    });
  }

  /**
   * Update data summary display
   */
  private updateDataSummary(data: ExperimentalData[]): void {
    const summary = this.dataLoader.getSummaryStatistics(data);
    const summaryDiv = document.getElementById('summary-stats');
    const dataSummary = document.getElementById('data-summary');
    
    if (summaryDiv && dataSummary) {
      summaryDiv.innerHTML = `
        <div class="summary-grid">
          <div><strong>Total Records:</strong> ${summary.totalRecords}</div>
          <div><strong>Mean Dose:</strong> ${formatNumber(summary.doseStatistics.mean, 2)} Gy</div>
          <div><strong>Dose Range:</strong> ${formatNumber(summary.doseStatistics.min, 2)} - ${formatNumber(summary.doseStatistics.max, 2)} Gy</div>
          <div><strong>Materials:</strong> ${summary.materials.join(', ')}</div>
          <div><strong>Sources:</strong> ${summary.sourceTypes.join(', ')}</div>
        </div>
      `;
      dataSummary.classList.remove('hidden');
    }
  }

  /**
   * Validate current data
   */
  private validateData(): void {
    if (this.currentData.length === 0) {
      this.showToast('No data to validate', 'warning');
      return;
    }

    const validation = this.dataLoader.validateData(this.currentData);
    
    if (validation.isValid) {
      this.showToast(`Data validation passed! ${validation.validRecords}/${validation.totalRecords} records valid`, 'success');
    } else {
      this.showToast(`Data validation failed: ${validation.errors.length} errors found`, 'error');
      console.log('Validation errors:', validation.errors);
      console.log('Validation warnings:', validation.warnings);
    }
  }

  /**
   * Export current data
   */
  private exportData(): void {
    if (this.currentData.length === 0) {
      this.showToast('No data to export', 'warning');
      return;
    }

    const csv = this.dataLoader.exportData(this.currentData, 'csv');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = 'experimental_data.csv';
    link.click();
    
    URL.revokeObjectURL(url);
    this.showToast('Data exported successfully', 'success');
  }

  /**
   * Plot dose distribution visualization
   */
  private plotDoseDistribution(): void {
    if (!this.currentResults) {
      this.showToast('Run a simulation first', 'warning');
      return;
    }

    const canvas = document.getElementById('viz-chart-1') as HTMLCanvasElement;
    if (canvas) {
      this.visualizer.plotDoseDistribution2D(canvas, this.currentResults, {
        title: 'Dose Distribution Visualization'
      });
    }
  }

  /**
   * Plot experimental vs simulation comparison
   */
  private async plotComparison(): Promise<void> {
    if (this.currentData.length === 0) {
      this.showToast('Load experimental data first', 'warning');
      return;
    }

    try {
      this.showLoading(true);
      
      const comparison = await this.simulator.compareWithExperimental(this.currentData);
      const canvas = document.getElementById('viz-chart-2') as HTMLCanvasElement;
      
      if (canvas) {
        this.visualizer.plotExperimentalComparison(
          canvas,
          comparison.experimentalData,
          comparison.simulationResults,
          { title: 'Experimental vs Simulation' }
        );
      }
      
      this.showToast(`Correlation: ${formatNumber(comparison.correlationCoefficient, 3)}`, 'info');
      
    } catch (error) {
      console.error('Comparison error:', error);
      this.showToast(`Comparison failed: ${error}`, 'error');
    } finally {
      this.showLoading(false);
    }
  }

  /**
   * Plot 3D visualization
   */
  private plot3D(): void {
    if (!this.currentResults) {
      this.showToast('Run a simulation first', 'warning');
      return;
    }

    const container = document.getElementById('viz-3d');
    if (container) {
      container.innerHTML = ''; // Clear previous content
      this.visualizer.plotDoseDistribution3D(container, this.currentResults, {
        title: '3D Dose Distribution'
      });
    }
  }

  /**
   * Plot statistics charts
   */
  private plotStatistics(): void {
    if (!this.currentResults) {
      this.showToast('Run a simulation first', 'warning');
      return;
    }

    const canvas = document.getElementById('viz-chart-4') as HTMLCanvasElement;
    if (canvas) {
      this.visualizer.plotDoseStatistics(canvas, this.currentResults, {
        title: 'Dose Statistics'
      });
    }
  }

  /**
   * Optimize exposure parameters
   */
  private async optimizeParameters(): Promise<void> {
    const targetDose = prompt('Enter target dose (Gy):');
    if (!targetDose || isNaN(parseFloat(targetDose))) {
      this.showToast('Invalid target dose', 'error');
      return;
    }

    try {
      this.showLoading(true);
      
      const params = this.getSimulationParameters();
      const optimized = await this.simulator.optimizeExposureParameters({
        targetDose: parseFloat(targetDose),
        materialName: params.material.name,
        sourceType: params.source,
        sourceActivity: params.sourceActivity,
        sourceDistance: params.sourceDistance
      });

      // Update exposure time input
      (document.getElementById('exposure-time') as HTMLInputElement).value = 
        formatNumber(optimized.exposureTime, 2);
      
      this.showToast(`Optimized exposure time: ${formatNumber(optimized.exposureTime, 2)} hours`, 'success');
      
    } catch (error) {
      console.error('Optimization error:', error);
      this.showToast(`Optimization failed: ${error}`, 'error');
    } finally {
      this.showLoading(false);
    }
  }

  /**
   * Load parameter preset
   */
  private loadPreset(): void {
    const presets = {
      'wheat-co60': {
        sourceType: 'Co-60',
        material: 'wheat',
        activity: 1000,
        distance: 50,
        exposureTime: 2.0,
        geometry: 'sphere',
        radius: 1.0
      },
      'rice-cs137': {
        sourceType: 'Cs-137',
        material: 'rice',
        activity: 800,
        distance: 60,
        exposureTime: 2.5,
        geometry: 'cylinder',
        radius: 1.0,
        height: 2.0
      }
    };

    const presetName = prompt('Enter preset name (wheat-co60, rice-cs137):') as keyof typeof presets;
    const preset = presets[presetName];
    
    if (preset) {
      this.setUIParameters(preset);
      this.showToast(`Loaded preset: ${presetName}`, 'success');
    } else {
      this.showToast('Unknown preset', 'error');
    }
  }

  /**
   * Set UI parameters from object
   */
  private setUIParameters(params: any): void {
    (document.getElementById('source-type') as HTMLSelectElement).value = params.sourceType;
    (document.getElementById('material') as HTMLSelectElement).value = params.material;
    (document.getElementById('activity') as HTMLInputElement).value = params.activity.toString();
    (document.getElementById('distance') as HTMLInputElement).value = params.distance.toString();
    (document.getElementById('exposure-time') as HTMLInputElement).value = params.exposureTime.toString();
    (document.getElementById('geometry') as HTMLSelectElement).value = params.geometry;
    
    this.updateGeometryInputs(params.geometry);
    
    if (params.radius) {
      (document.getElementById('radius') as HTMLInputElement).value = params.radius.toString();
      (document.getElementById('cyl-radius') as HTMLInputElement).value = params.radius.toString();
    }
    if (params.height) {
      (document.getElementById('height') as HTMLInputElement).value = params.height.toString();
    }
  }

  /**
   * Save current results
   */
  private saveResults(): void {
    if (!this.currentResults) {
      this.showToast('No results to save', 'warning');
      return;
    }

    const data = JSON.stringify(this.currentResults, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `simulation_results_${Date.now()}.json`;
    link.click();
    
    URL.revokeObjectURL(url);
    this.showToast('Results saved successfully', 'success');
  }

  /**
   * Generate detailed report
   */
  private generateReport(): void {
    if (!this.currentResults) {
      this.showToast('No results to report', 'warning');
      return;
    }

    const report = this.createDetailedReport(this.currentResults);
    const detailedResults = document.getElementById('detailed-results');
    
    if (detailedResults) {
      detailedResults.innerHTML = report;
      this.switchTab('results');
    }
  }

  /**
   * Create detailed HTML report
   */
  private createDetailedReport(results: SimulationResults): string {
    return `
      <div class="report">
        <h3>Simulation Report</h3>
        <div class="report-section">
          <h4>Parameters</h4>
          <ul>
            <li><strong>Source:</strong> ${results.parameters.source}</li>
            <li><strong>Material:</strong> ${results.parameters.material.name}</li>
            <li><strong>Activity:</strong> ${formatNumber(results.parameters.sourceActivity, 0)} Ci</li>
            <li><strong>Distance:</strong> ${formatNumber(results.parameters.sourceDistance, 1)} cm</li>
            <li><strong>Exposure Time:</strong> ${formatNumber(results.parameters.exposureTime, 2)} hours</li>
            <li><strong>Geometry:</strong> ${results.parameters.geometry.shape}</li>
          </ul>
        </div>
        <div class="report-section">
          <h4>Results</h4>
          <ul>
            <li><strong>Uniform Dose:</strong> ${formatNumber(results.uniformDose, 3)} Gy</li>
            <li><strong>Mean Dose:</strong> ${formatNumber(results.meanDose, 3)} Gy</li>
            <li><strong>Max Dose:</strong> ${formatNumber(results.maxDose, 3)} Gy</li>
            <li><strong>Min Dose:</strong> ${formatNumber(results.minDose, 3)} Gy</li>
            <li><strong>Dose Uniformity:</strong> ${formatNumber(results.doseUniformity, 3)}</li>
            <li><strong>Computation Time:</strong> ${formatNumber(results.computationTime, 3)} s</li>
          </ul>
        </div>
        <div class="report-section">
          <h4>Material Properties</h4>
          <ul>
            <li><strong>Density:</strong> ${formatNumber(results.parameters.material.density, 2)} g/cm³</li>
            <li><strong>Atomic Number:</strong> ${formatNumber(results.parameters.material.atomicNumber, 1)}</li>
            <li><strong>Mass Attenuation Coefficient:</strong> ${formatNumber(results.parameters.material.massAttenuationCoefficient, 4)} cm²/g</li>
          </ul>
        </div>
        <p class="timestamp">Generated on: ${new Date(results.timestamp).toLocaleString()}</p>
      </div>
    `;
  }

  /**
   * Export visualization images
   */
  private exportImages(): void {
    // This would export current charts as images
    this.showToast('Image export feature coming soon!', 'info');
  }

  /**
   * Handle parameter changes
   */
  private onParameterChange(): void {
    this.emit('parameterChanged', this.getSimulationParameters());
  }

  /**
   * Save parameters to localStorage
   */
  private saveParameters(): void {
    try {
      const params = this.getSimulationParameters();
      storage.set('simulation-parameters', params);
    } catch (error) {
      // Ignore errors when saving parameters
    }
  }

  /**
   * Load stored parameters from localStorage
   */
  private loadStoredParameters(): void {
    const stored = storage.get('simulation-parameters');
    if (stored) {
      try {
        this.setUIParameters(stored);
      } catch (error) {
        console.warn('Failed to load stored parameters:', error);
      }
    }
  }

  /**
   * Show/hide loading overlay
   */
  private showLoading(show: boolean): void {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
      overlay.classList.toggle('hidden', !show);
    }
  }

  /**
   * Show toast notification
   */
  private showToast(message: string, type: 'success' | 'error' | 'warning' | 'info' = 'info'): void {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    // Auto remove after 5 seconds
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 5000);

    // Allow manual removal
    toast.addEventListener('click', () => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    });
  }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new GrainIrradiationApp();
});