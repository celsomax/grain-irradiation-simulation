import { Chart, ChartConfiguration, registerables } from 'chart.js';
import * as THREE from 'three';
import { SimulationResults } from '../core/simulator.js';
import { ExperimentalData, DataSummary } from '../data/loader.js';

// Register Chart.js components
Chart.register(...registerables);

/**
 * Visualization options for different chart types
 */
export interface VisualizationOptions {
  width?: number;
  height?: number;
  colormap?: string;
  showLegend?: boolean;
  showGrid?: boolean;
  title?: string;
  responsive?: boolean;
}

/**
 * Main visualization class for creating charts and 3D plots
 */
export class Visualizer {
  private charts: Map<string, Chart> = new Map();
  private renderers: Map<string, THREE.WebGLRenderer> = new Map();

  /**
   * Create a 2D dose distribution plot using Chart.js
   */
  plotDoseDistribution2D(
    container: HTMLCanvasElement,
    results: SimulationResults,
    options: VisualizationOptions = {}
  ): Chart {
    if (!results.doseDistribution || !results.coordinates) {
      throw new Error('Dose distribution data not available');
    }

    const doseMatrix = results.doseDistribution;
    const { x, y } = results.coordinates;

    // Prepare data for heatmap
    const data: any[] = [];
    for (let i = 0; i < doseMatrix.length; i++) {
      for (let j = 0; j < doseMatrix[i].length; j++) {
        if (doseMatrix[i][j] > 0) {
          data.push({
            x: x[i],
            y: y[j],
            v: doseMatrix[i][j]
          });
        }
      }
    }

    const config: ChartConfiguration = {
      type: 'scatter',
      data: {
        datasets: [{
          label: 'Dose Distribution',
          data: data.map(point => ({ x: point.x, y: point.y })),
          backgroundColor: data.map(point => this.getColorForDose(point.v, results.maxDose)),
          pointRadius: 3,
          pointHoverRadius: 5
        }]
      },
      options: {
        responsive: options.responsive !== false,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: !!options.title,
            text: options.title || 'Dose Distribution (2D)'
          },
          legend: {
            display: options.showLegend !== false
          },
          tooltip: {
            callbacks: {
              label: function(context: any) {
                const point = data[context.dataIndex];
                return `Dose: ${point.v.toFixed(3)} Gy`;
              }
            }
          }
        },
        scales: {
          x: {
            type: 'linear',
            title: {
              display: true,
              text: 'X Position (cm)'
            },
            grid: {
              display: options.showGrid !== false
            }
          },
          y: {
            type: 'linear',
            title: {
              display: true,
              text: 'Y Position (cm)'
            },
            grid: {
              display: options.showGrid !== false
            }
          }
        }
      }
    };

    const chart = new Chart(container, config);
    this.charts.set(container.id, chart);
    return chart;
  }

  /**
   * Create a 3D dose distribution visualization using Three.js
   */
  plotDoseDistribution3D(
    container: HTMLElement,
    results: SimulationResults,
    options: VisualizationOptions = {}
  ): THREE.WebGLRenderer {
    if (!results.doseDistribution || !results.coordinates) {
      throw new Error('Dose distribution data not available');
    }

    const width = options.width || container.clientWidth;
    const height = options.height || container.clientHeight;

    // Create scene, camera, and renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });

    renderer.setSize(width, height);
    renderer.setClearColor(0xf0f0f0);
    container.appendChild(renderer.domElement);

    // Create dose distribution visualization
    this.create3DDoseVisualization(scene, results);

    // Position camera
    camera.position.set(5, 5, 5);
    camera.lookAt(0, 0, 0);

    // Add controls (you would need OrbitControls import for this)
    // const controls = new OrbitControls(camera, renderer.domElement);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(1, 1, 0.5);
    scene.add(directionalLight);

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      // controls.update();
      renderer.render(scene, camera);
    };
    animate();

    this.renderers.set(container.id, renderer);
    return renderer;
  }

  /**
   * Create dose statistics chart
   */
  plotDoseStatistics(
    container: HTMLCanvasElement,
    results: SimulationResults,
    options: VisualizationOptions = {}
  ): Chart {
    const data = {
      labels: ['Uniform Dose', 'Mean Dose', 'Max Dose', 'Min Dose'],
      datasets: [{
        label: 'Dose (Gy)',
        data: [results.uniformDose, results.meanDose, results.maxDose, results.minDose],
        backgroundColor: [
          'rgba(54, 162, 235, 0.6)',
          'rgba(75, 192, 192, 0.6)',
          'rgba(255, 99, 132, 0.6)',
          'rgba(255, 205, 86, 0.6)'
        ],
        borderColor: [
          'rgba(54, 162, 235, 1)',
          'rgba(75, 192, 192, 1)',
          'rgba(255, 99, 132, 1)',
          'rgba(255, 205, 86, 1)'
        ],
        borderWidth: 1
      }]
    };

    const config: ChartConfiguration = {
      type: 'bar',
      data,
      options: {
        responsive: options.responsive !== false,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: !!options.title,
            text: options.title || 'Dose Statistics'
          },
          legend: {
            display: options.showLegend !== false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Dose (Gy)'
            }
          }
        }
      }
    };

    const chart = new Chart(container, config);
    this.charts.set(container.id, chart);
    return chart;
  }

  /**
   * Create experimental vs simulation comparison chart
   */
  plotExperimentalComparison(
    container: HTMLCanvasElement,
    experimentalData: ExperimentalData[],
    simulationResults: SimulationResults[],
    options: VisualizationOptions = {}
  ): Chart {
    const expDoses = experimentalData.map(exp => exp.dose);
    const simDoses = simulationResults.map(sim => sim.uniformDose);

    const config: ChartConfiguration = {
      type: 'scatter',
      data: {
        datasets: [{
          label: 'Experimental vs Simulation',
          data: expDoses.map((exp, i) => ({ x: exp, y: simDoses[i] || 0 })),
          backgroundColor: 'rgba(75, 192, 192, 0.6)',
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 1
        }, {
          label: 'Perfect Correlation',
          data: [
            { x: Math.min(...expDoses), y: Math.min(...expDoses) },
            { x: Math.max(...expDoses), y: Math.max(...expDoses) }
          ],
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          borderColor: 'rgba(255, 99, 132, 1)',
          borderWidth: 2,
          pointRadius: 0,
          fill: false,
          showLine: true
        }]
      },
      options: {
        responsive: options.responsive !== false,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: !!options.title,
            text: options.title || 'Experimental vs Simulation Comparison'
          },
          legend: {
            display: options.showLegend !== false
          }
        },
        scales: {
          x: {
            type: 'linear',
            title: {
              display: true,
              text: 'Experimental Dose (Gy)'
            }
          },
          y: {
            type: 'linear',
            title: {
              display: true,
              text: 'Simulated Dose (Gy)'
            }
          }
        }
      }
    };

    const chart = new Chart(container, config);
    this.charts.set(container.id, chart);
    return chart;
  }

  /**
   * Create data summary charts
   */
  plotDataSummary(
    container: HTMLCanvasElement,
    summary: DataSummary,
    chartType: 'materials' | 'sources' | 'dose_histogram',
    options: VisualizationOptions = {}
  ): Chart {
    let config: ChartConfiguration;

    switch (chartType) {
      case 'materials':
        config = this.createMaterialDistributionChart(summary, options);
        break;
      case 'sources':
        config = this.createSourceDistributionChart(summary, options);
        break;
      case 'dose_histogram':
        config = this.createDoseHistogramChart(summary, options);
        break;
      default:
        throw new Error(`Unknown chart type: ${chartType}`);
    }

    const chart = new Chart(container, config);
    this.charts.set(container.id, chart);
    return chart;
  }

  /**
   * Export chart as image
   */
  exportChart(chartId: string, format: 'png' | 'jpeg' = 'png'): string {
    const chart = this.charts.get(chartId);
    if (!chart) {
      throw new Error(`Chart with id ${chartId} not found`);
    }

    return chart.toBase64Image(`image/${format}`, 1.0);
  }

  /**
   * Clean up charts and renderers
   */
  cleanup(): void {
    this.charts.forEach(chart => chart.destroy());
    this.charts.clear();

    this.renderers.forEach(renderer => {
      renderer.dispose();
      if (renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(renderer.domElement);
      }
    });
    this.renderers.clear();
  }

  /**
   * Get color for dose value (for heatmap)
   */
  private getColorForDose(dose: number, maxDose: number): string {
    const intensity = dose / maxDose;
    const red = Math.floor(255 * intensity);
    const blue = Math.floor(255 * (1 - intensity));
    return `rgba(${red}, 0, ${blue}, 0.7)`;
  }

  /**
   * Create 3D dose visualization geometry
   */
  private create3DDoseVisualization(scene: THREE.Scene, results: SimulationResults): void {
    if (!results.doseDistribution || !results.coordinates) return;

    const doseMatrix = results.doseDistribution;
    const { x, y } = results.coordinates;

    const geometry = new THREE.BufferGeometry();
    const vertices: number[] = [];
    const colors: number[] = [];

    for (let i = 0; i < doseMatrix.length; i++) {
      for (let j = 0; j < doseMatrix[i].length; j++) {
        const dose = doseMatrix[i][j];
        if (dose > 0) {
          const height = (dose / results.maxDose) * 2; // Scale height
          
          // Create a small cube at this position
          vertices.push(x[i] / 10, height / 2, y[j] / 10); // Scale down coordinates
          
          // Color based on dose intensity
          const intensity = dose / results.maxDose;
          colors.push(intensity, 0, 1 - intensity);
        }
      }
    }

    geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
    geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

    const material = new THREE.PointsMaterial({
      size: 0.1,
      vertexColors: true
    });

    const points = new THREE.Points(geometry, material);
    scene.add(points);
  }

  /**
   * Create material distribution chart config
   */
  private createMaterialDistributionChart(
    summary: DataSummary,
    options: VisualizationOptions
  ): ChartConfiguration {
    return {
      type: 'pie',
      data: {
        labels: Object.keys(summary.materialCounts),
        datasets: [{
          data: Object.values(summary.materialCounts),
          backgroundColor: [
            'rgba(255, 99, 132, 0.6)',
            'rgba(54, 162, 235, 0.6)',
            'rgba(255, 205, 86, 0.6)',
            'rgba(75, 192, 192, 0.6)'
          ]
        }]
      },
      options: {
        responsive: options.responsive !== false,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: !!options.title,
            text: options.title || 'Material Distribution'
          },
          legend: {
            display: options.showLegend !== false
          }
        }
      }
    };
  }

  /**
   * Create source distribution chart config
   */
  private createSourceDistributionChart(
    summary: DataSummary,
    options: VisualizationOptions
  ): ChartConfiguration {
    return {
      type: 'doughnut',
      data: {
        labels: Object.keys(summary.sourceTypeCounts),
        datasets: [{
          data: Object.values(summary.sourceTypeCounts),
          backgroundColor: [
            'rgba(255, 159, 64, 0.6)',
            'rgba(153, 102, 255, 0.6)',
            'rgba(201, 203, 207, 0.6)'
          ]
        }]
      },
      options: {
        responsive: options.responsive !== false,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: !!options.title,
            text: options.title || 'Source Type Distribution'
          },
          legend: {
            display: options.showLegend !== false
          }
        }
      }
    };
  }

  /**
   * Create dose histogram chart config
   */
  private createDoseHistogramChart(
    summary: DataSummary,
    options: VisualizationOptions
  ): ChartConfiguration {
    // Create histogram bins (simplified)
    const bins = 10;
    const binSize = (summary.doseStatistics.max - summary.doseStatistics.min) / bins;
    const labels = [];
    const data = new Array(bins).fill(0);

    for (let i = 0; i < bins; i++) {
      const binStart = summary.doseStatistics.min + i * binSize;
      const binEnd = binStart + binSize;
      labels.push(`${binStart.toFixed(1)}-${binEnd.toFixed(1)}`);
    }

    return {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Frequency',
          data,
          backgroundColor: 'rgba(75, 192, 192, 0.6)',
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: options.responsive !== false,
        maintainAspectRatio: false,
        plugins: {
          title: {
            display: !!options.title,
            text: options.title || 'Dose Distribution Histogram'
          },
          legend: {
            display: options.showLegend !== false
          }
        },
        scales: {
          x: {
            title: {
              display: true,
              text: 'Dose Range (Gy)'
            }
          },
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Frequency'
            }
          }
        }
      }
    };
  }
}