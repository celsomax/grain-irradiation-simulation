# 🌾 Grain Irradiation Simulation - JavaScript Edition

[![Deploy Status](https://github.com/celsomax/grain-irradiation-simulation/actions/workflows/deploy.yml/badge.svg)](https://github.com/celsomax/grain-irradiation-simulation/actions/workflows/deploy.yml)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-646CFF?logo=vite&logoColor=white)](https://vitejs.dev/)
[![PWA](https://img.shields.io/badge/PWA-Ready-purple)](https://web.dev/progressive-web-apps/)

A modern, interactive web application for simulating grain and seed irradiation processes. This JavaScript/TypeScript version provides enhanced user experience with real-time visualizations and progressive web app capabilities.

## 🚀 **Live Demo**

Visit the deployed application: [**Grain Simulation App**](https://celsomax.github.io/grain-irradiation-simulation/)

## ✨ **Features**

### **Core Simulation Engine**
- **Physics-based calculations**: Validated radiation dose models
- **Multiple radiation sources**: Cobalt-60, Cesium-137, Linear Accelerators
- **Material support**: Wheat, rice, corn, water with accurate physical properties
- **Geometry modeling**: Spherical, cylindrical, and box-shaped samples
- **Spatial dose distribution**: 2D and 3D dose mapping

### **Modern Web Interface**
- **Responsive design**: Works on desktop, tablet, and mobile devices
- **Real-time visualization**: Interactive charts and 3D graphics
- **Progressive Web App**: Install and use offline
- **Dark mode support**: Automatic theme adaptation
- **Touch-friendly**: Optimized for mobile interaction

### **Advanced Capabilities**
- **Parameter optimization**: Automatic exposure time calculation
- **Experimental data integration**: Load and validate CSV/JSON data
- **Comparison analysis**: Experimental vs simulation correlation
- **Data export**: Results in JSON, CSV, and image formats
- **Batch processing**: Multiple simulation scenarios

## 🛠 **Technology Stack**

- **Frontend**: TypeScript, HTML5, CSS3
- **Build Tool**: Vite with HMR and optimization
- **Visualization**: Chart.js, Three.js, D3.js
- **PWA**: Service Worker, offline capabilities
- **Deployment**: GitHub Pages with automated CI/CD

## 📦 **Installation**

### **Prerequisites**
- Node.js 18+ and npm
- Modern web browser with ES2020 support

### **Development Setup**

```bash
# Clone the repository
git clone https://github.com/celsomax/grain-irradiation-simulation.git
cd grain-irradiation-simulation

# Install dependencies
npm install

# Start development server
npm run dev
```

### **Production Build**

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## 🎯 **Quick Start**

### **1. Basic Simulation**

1. **Open the application** in your browser
2. **Set parameters** in the simulation panel:
   - Source: Co-60 (1000 Ci)
   - Material: Wheat
   - Distance: 50 cm
   - Time: 2 hours
3. **Click "Run Simulation"** to see results
4. **View dose distribution** in the live chart

### **2. Load Experimental Data**

```javascript
// Sample data format (CSV/JSON)
const experimentalData = [
  {
    sample_id: "WH001",
    material: "wheat",
    dose: 2.5,
    source_type: "Co-60",
    source_activity: 1000,
    distance: 50,
    exposure_time: 2.0
  }
];
```

### **3. Parameter Optimization**

```javascript
// Find optimal exposure time for target dose
const optimizedParams = await simulator.optimizeExposureParameters({
  targetDose: 5.0,
  materialName: "rice",
  sourceType: "Co-60",
  sourceActivity: 800,
  sourceDistance: 60
});
```

## 📊 **API Reference**

### **Core Classes**

#### **IrradiationSimulator**
```typescript
class IrradiationSimulator {
  // Create simulation parameters
  createSimulationParameters(config: SimulationConfig): SimulationParameters;
  
  // Run single simulation
  runSimulation(params: SimulationParameters): Promise<SimulationResults>;
  
  // Run batch simulations
  runBatchSimulation(parameterSets: SimulationParameters[]): Promise<SimulationResults[]>;
  
  // Compare with experimental data
  compareWithExperimental(data: ExperimentalData[]): Promise<ComparisonResults>;
  
  // Optimize parameters
  optimizeExposureParameters(config: OptimizationConfig): Promise<SimulationParameters>;
}
```

#### **DataLoader**
```typescript
class DataLoader {
  // Load data from file or string
  loadData(input: string | File | ExperimentalData[]): Promise<ExperimentalData[]>;
  
  // Validate data quality
  validateData(data: ExperimentalData[]): DataValidationResult;
  
  // Generate statistics
  getSummaryStatistics(data: ExperimentalData[]): DataSummary;
  
  // Filter data
  filterData(data: ExperimentalData[], criteria: FilterCriteria): ExperimentalData[];
}
```

#### **Visualizer**
```typescript
class Visualizer {
  // 2D dose distribution plot
  plotDoseDistribution2D(canvas: HTMLCanvasElement, results: SimulationResults): Chart;
  
  // 3D visualization
  plotDoseDistribution3D(container: HTMLElement, results: SimulationResults): THREE.WebGLRenderer;
  
  // Experimental comparison
  plotExperimentalComparison(canvas: HTMLCanvasElement, experimental: ExperimentalData[], simulated: SimulationResults[]): Chart;
  
  // Statistics charts
  plotDoseStatistics(canvas: HTMLCanvasElement, results: SimulationResults): Chart;
}
```

## 🔬 **Scientific Background**

### **Physics Models**

- **Dose Rate Calculation**: Inverse square law for point sources
- **Attenuation**: Beer-Lambert law for material penetration  
- **Spatial Distribution**: Monte Carlo-inspired dose mapping
- **Source Modeling**: Validated properties for common sources

### **Material Properties**

| Material | Density (g/cm³) | Z_eff | μ/ρ (cm²/g) |
|----------|-----------------|-------|-------------|
| Wheat    | 0.80           | 6.5   | 0.0302      |
| Rice     | 0.75           | 6.3   | 0.0298      |
| Corn     | 0.85           | 6.7   | 0.0305      |
| Water    | 1.00           | 7.4   | 0.0270      |

### **Radiation Sources**

| Source    | Energy (MeV) | Half-life | Dose Rate Constant |
|-----------|--------------|-----------|-------------------|
| Co-60     | 1.25         | 5.27 yr   | 1.32 R·m²/(h·Ci)  |
| Cs-137    | 0.662        | 30.1 yr   | 0.325 R·m²/(h·Ci) |
| LinAc     | 10.0         | N/A       | Variable          |

## 📱 **Progressive Web App**

The application can be installed as a PWA:

1. **Open the app** in a modern browser
2. **Look for "Install App"** prompt in address bar
3. **Click to install** for native-like experience
4. **Use offline** with cached resources

### **PWA Features**
- ✅ Offline functionality
- ✅ App-like experience
- ✅ Push notifications (future)
- ✅ Background sync (future)

## 🎨 **User Interface**

### **Navigation Tabs**
- **Simulation**: Parameter input and quick results
- **Data**: Experimental data management
- **Visualization**: Interactive charts and 3D plots
- **Results**: Detailed reports and export

### **Key Components**
- **Parameter Panel**: Real-time input validation
- **Live Charts**: Immediate dose distribution preview
- **Data Table**: Sortable experimental data view
- **3D Viewer**: Interactive dose visualization

## 📁 **Project Structure**

```
src/
├── core/                    # Core simulation engine
│   ├── physics.ts          # Physical models
│   └── simulator.ts        # Main simulation logic
├── data/                   # Data handling
│   └── loader.ts          # Import/export/validation
├── visualization/          # Charts and 3D graphics
│   └── charts.ts          # Visualization components
├── ui/                     # User interface
│   ├── components/        # Reusable UI components
│   ├── views/            # Main application views
│   └── styles/           # CSS styles
├── utils/                 # Utility functions
│   ├── math.ts           # Mathematical operations
│   └── helpers.ts        # General utilities
└── main.ts               # Application entry point
```

## 🧪 **Testing**

```bash
# Run type checking
npm run type-check

# Run linting
npm run lint

# Fix linting issues
npm run lint:fix

# Run tests (future)
npm run test
```

## 🚀 **Deployment**

### **GitHub Pages**
The application automatically deploys to GitHub Pages on push to main branch.

### **Custom Deployment**
```bash
# Build for production
npm run build

# Deploy dist/ folder to your hosting service
```

### **Docker Deployment**
```dockerfile
FROM nginx:alpine
COPY dist/ /usr/share/nginx/html/
EXPOSE 80
```

## 🔧 **Configuration**

### **Vite Configuration**
```typescript
// vite.config.ts
export default defineConfig({
  base: './',  // For GitHub Pages
  build: {
    outDir: 'dist',
    sourcemap: true
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  }
});
```

### **TypeScript Configuration**
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "strict": true,
    "moduleResolution": "bundler"
  }
}
```

## 🤝 **Contributing**

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Make changes** and add tests
4. **Run quality checks**: `npm run lint && npm run type-check`
5. **Commit changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open Pull Request**

### **Development Guidelines**
- Use TypeScript for type safety
- Follow ESLint configuration
- Write comprehensive JSDoc comments
- Maintain backwards compatibility
- Test on multiple browsers

## 📚 **Documentation**

- **[API Documentation](docs/api.md)** - Detailed API reference
- **[User Guide](docs/user-guide.md)** - Step-by-step tutorials
- **[Physics Background](docs/physics.md)** - Scientific foundations
- **[Deployment Guide](docs/deployment.md)** - Hosting instructions

## 🔗 **Comparison with Python Version**

| Feature | Python | JavaScript | Notes |
|---------|--------|------------|-------|
| Physics Engine | ✅ | ✅ | Identical calculations |
| Data Handling | ✅ | ✅ | Enhanced web formats |
| Visualization | ✅ | ✅ | Interactive 3D graphics |
| User Interface | Tkinter | Modern Web | Responsive design |
| Platform | Desktop | Cross-platform | Browser-based |
| Installation | pip install | Web app | No installation needed |
| Offline Support | ✅ | ✅ | PWA capabilities |

## 📄 **License**

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- Original Python implementation contributors
- Scientific references and validation data
- Open-source visualization libraries
- Web development community

## 📞 **Support**

- **Issues**: [GitHub Issues](https://github.com/celsomax/grain-irradiation-simulation/issues)
- **Discussions**: [GitHub Discussions](https://github.com/celsomax/grain-irradiation-simulation/discussions)
- **Wiki**: [Project Wiki](https://github.com/celsomax/grain-irradiation-simulation/wiki)

---

**Made with ❤️ for the food irradiation research community**