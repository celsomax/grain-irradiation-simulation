"""
Graphical User Interface for grain irradiation simulation.

This module provides a simple Tkinter-based GUI for users who prefer
a graphical interface over command line.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from pathlib import Path
import json
import logging
from typing import Optional, Dict, Any

from ..core.simulator import IrradiationSimulator
from ..data.loader import DataLoader
from ..visualization.plotter import DoseVisualizer

# Configure logging
logger = logging.getLogger(__name__)


class SimulationGUI:
    """Main GUI application for grain irradiation simulation."""
    
    def __init__(self, root: tk.Tk):
        """Initialize the GUI application."""
        self.root = root
        self.root.title("Grain Irradiation Simulation Tool")
        self.root.geometry("900x700")
        
        # Initialize components
        self.simulator = IrradiationSimulator()
        self.data_loader = DataLoader()
        self.visualizer = DoseVisualizer()
        
        # Variables
        self.simulation_running = False
        self.current_results = None
        
        # Setup GUI
        self.setup_gui()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_gui(self):
        """Setup the GUI layout and components."""
        # Create main notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.setup_simulation_tab()
        self.setup_data_tab()
        self.setup_results_tab()
        self.setup_settings_tab()
    
    def setup_simulation_tab(self):
        """Setup the simulation parameters tab."""
        # Create simulation frame
        sim_frame = ttk.Frame(self.notebook)
        self.notebook.add(sim_frame, text="Simulation")
        
        # Main container with scrollbar
        canvas = tk.Canvas(sim_frame)
        scrollbar = ttk.Scrollbar(sim_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Source parameters
        source_frame = ttk.LabelFrame(scrollable_frame, text="Radiation Source", padding=10)
        source_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(source_frame, text="Source Type:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.source_var = tk.StringVar(value="Co-60")
        source_combo = ttk.Combobox(source_frame, textvariable=self.source_var, 
                                   values=["Co-60", "Cs-137", "LinAc"], state="readonly")
        source_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(source_frame, text="Activity:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.activity_var = tk.StringVar(value="1000")
        ttk.Entry(source_frame, textvariable=self.activity_var, width=15).grid(
            row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        ttk.Label(source_frame, text="(Ci for isotopes, kW for LinAc)").grid(
            row=1, column=2, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(source_frame, text="Distance (cm):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.distance_var = tk.StringVar(value="50")
        ttk.Entry(source_frame, textvariable=self.distance_var, width=15).grid(
            row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Material parameters
        material_frame = ttk.LabelFrame(scrollable_frame, text="Material Properties", padding=10)
        material_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(material_frame, text="Material:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.material_var = tk.StringVar(value="wheat")
        material_combo = ttk.Combobox(material_frame, textvariable=self.material_var,
                                     values=["wheat", "rice", "corn", "water"], state="readonly")
        material_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Geometry parameters
        geometry_frame = ttk.LabelFrame(scrollable_frame, text="Sample Geometry", padding=10)
        geometry_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(geometry_frame, text="Shape:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.geometry_var = tk.StringVar(value="sphere")
        geometry_combo = ttk.Combobox(geometry_frame, textvariable=self.geometry_var,
                                     values=["sphere", "cylinder", "box"], state="readonly")
        geometry_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(geometry_frame, text="Size (cm):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.geometry_size_var = tk.StringVar(value="1.0")
        ttk.Entry(geometry_frame, textvariable=self.geometry_size_var, width=15).grid(
            row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        ttk.Label(geometry_frame, text="(radius for sphere, side for box)").grid(
            row=1, column=2, sticky=tk.W, padx=(5, 0), pady=2)
        
        # Exposure parameters
        exposure_frame = ttk.LabelFrame(scrollable_frame, text="Exposure Parameters", padding=10)
        exposure_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(exposure_frame, text="Exposure Time (h):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.time_var = tk.StringVar(value="2.0")
        ttk.Entry(exposure_frame, textvariable=self.time_var, width=15).grid(
            row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(exposure_frame, text="Temperature (°C):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.temperature_var = tk.StringVar()
        ttk.Entry(exposure_frame, textvariable=self.temperature_var, width=15).grid(
            row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        ttk.Label(exposure_frame, text="(optional)").grid(
            row=1, column=2, sticky=tk.W, padx=(5, 0), pady=2)
        
        ttk.Label(exposure_frame, text="Humidity (%):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.humidity_var = tk.StringVar()
        ttk.Entry(exposure_frame, textvariable=self.humidity_var, width=15).grid(
            row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        ttk.Label(exposure_frame, text="(optional)").grid(
            row=2, column=2, sticky=tk.W, padx=(5, 0), pady=2)
        
        # Simulation options
        options_frame = ttk.LabelFrame(scrollable_frame, text="Simulation Options", padding=10)
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.calc_distribution_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Calculate dose distribution", 
                       variable=self.calc_distribution_var).pack(anchor=tk.W)
        
        self.generate_plots_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Generate visualization plots", 
                       variable=self.generate_plots_var).pack(anchor=tk.W)
        
        # Buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.run_button = ttk.Button(button_frame, text="Run Simulation", 
                                    command=self.run_simulation)
        self.run_button.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Save Parameters", 
                  command=self.save_parameters).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="Load Parameters", 
                  command=self.load_parameters).pack(side=tk.LEFT)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_data_tab(self):
        """Setup the data loading and analysis tab."""
        data_frame = ttk.Frame(self.notebook)
        self.notebook.add(data_frame, text="Experimental Data")
        
        # File selection
        file_frame = ttk.LabelFrame(data_frame, text="Data File", padding=10)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.data_file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.data_file_var, width=50).pack(
            side=tk.LEFT, padx=(0, 10))
        ttk.Button(file_frame, text="Browse", command=self.browse_data_file).pack(side=tk.LEFT)
        
        # Data operations
        operations_frame = ttk.LabelFrame(data_frame, text="Data Operations", padding=10)
        operations_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(operations_frame, text="Load Data", 
                  command=self.load_data).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(operations_frame, text="Validate Data", 
                  command=self.validate_data).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(operations_frame, text="Generate Summary", 
                  command=self.generate_summary).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(operations_frame, text="Compare with Simulation", 
                  command=self.compare_data).pack(side=tk.LEFT)
        
        # Data display
        display_frame = ttk.LabelFrame(data_frame, text="Data Information", padding=10)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.data_text = scrolledtext.ScrolledText(display_frame, height=20, width=80)
        self.data_text.pack(fill=tk.BOTH, expand=True)
        
        # Store loaded data
        self.experimental_data = None
    
    def setup_results_tab(self):
        """Setup the results display tab."""
        results_frame = ttk.Frame(self.notebook)
        self.notebook.add(results_frame, text="Results")
        
        # Results display
        self.results_text = scrolledtext.ScrolledText(results_frame, height=25, width=80)
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Results buttons
        button_frame = ttk.Frame(results_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Save Results", 
                  command=self.save_results).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Generate Report", 
                  command=self.generate_report).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Clear Results", 
                  command=self.clear_results).pack(side=tk.LEFT)
    
    def setup_settings_tab(self):
        """Setup the settings and configuration tab."""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Visualization settings
        viz_frame = ttk.LabelFrame(settings_frame, text="Visualization Settings", padding=10)
        viz_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(viz_frame, text="Output Directory:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.output_dir_var = tk.StringVar(value="./plots")
        ttk.Entry(viz_frame, textvariable=self.output_dir_var, width=40).grid(
            row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        ttk.Button(viz_frame, text="Browse", 
                  command=self.browse_output_dir).grid(row=0, column=2, padx=(10, 0), pady=2)
        
        # Logging settings
        log_frame = ttk.LabelFrame(settings_frame, text="Logging", padding=10)
        log_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(log_frame, text="Log Level:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.log_level_var = tk.StringVar(value="INFO")
        log_combo = ttk.Combobox(log_frame, textvariable=self.log_level_var,
                                values=["DEBUG", "INFO", "WARNING", "ERROR"], state="readonly")
        log_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # About
        about_frame = ttk.LabelFrame(settings_frame, text="About", padding=10)
        about_frame.pack(fill=tk.X, padx=5, pady=5)
        
        about_text = """Grain Irradiation Simulation Tool v0.1.0
        
A Python software for simulating grain and seed irradiation processes.
Developed for educational and research purposes.

Features:
• Physics-based dose calculations
• Multiple radiation sources (Co-60, Cs-137, Linear Accelerators)
• Various sample geometries
• Experimental data comparison
• 2D/3D visualization
• CLI and GUI interfaces

For more information, documentation, and source code:
https://github.com/celsomax/grain-irradiation-simulation"""
        
        about_label = tk.Label(about_frame, text=about_text, justify=tk.LEFT, 
                              wraplength=600, font=("TkDefaultFont", 9))
        about_label.pack(anchor=tk.W)
    
    def run_simulation(self):
        """Run the irradiation simulation in a separate thread."""
        if self.simulation_running:
            messagebox.showwarning("Warning", "Simulation already running!")
            return
        
        try:
            # Validate inputs
            activity = float(self.activity_var.get())
            distance = float(self.distance_var.get())
            time = float(self.time_var.get())
            geometry_size = float(self.geometry_size_var.get())
            
            temperature = None
            if self.temperature_var.get().strip():
                temperature = float(self.temperature_var.get())
            
            humidity = None
            if self.humidity_var.get().strip():
                humidity = float(self.humidity_var.get())
            
        except ValueError as e:
            messagebox.showerror("Input Error", f"Invalid input: {e}")
            return
        
        # Disable run button
        self.run_button.config(state="disabled", text="Running...")
        self.simulation_running = True
        
        # Run simulation in thread
        def simulation_thread():
            try:
                # Create geometry configuration
                geometry_shape = self.geometry_var.get()
                if geometry_shape == 'sphere':
                    geometry_config = {
                        'shape': 'sphere',
                        'dimensions': {'radius': geometry_size}
                    }
                elif geometry_shape == 'cylinder':
                    geometry_config = {
                        'shape': 'cylinder',
                        'dimensions': {'radius': geometry_size, 'height': geometry_size * 2}
                    }
                else:  # box
                    geometry_config = {
                        'shape': 'box',
                        'dimensions': {
                            'length': geometry_size,
                            'width': geometry_size,
                            'height': geometry_size
                        }
                    }
                
                # Create simulation parameters
                params = self.simulator.create_simulation_parameters(
                    source_type=self.source_var.get(),
                    material_name=self.material_var.get(),
                    source_activity=activity,
                    source_distance=distance,
                    exposure_time=time,
                    geometry_config=geometry_config,
                    temperature=temperature,
                    humidity=humidity
                )
                
                # Run simulation
                calculate_distribution = self.calc_distribution_var.get()
                results = self.simulator.run_simulation(params, calculate_distribution)
                
                # Update GUI in main thread
                self.root.after(0, lambda: self.simulation_completed(results))
                
            except Exception as e:
                self.root.after(0, lambda: self.simulation_error(str(e)))
        
        threading.Thread(target=simulation_thread, daemon=True).start()
    
    def simulation_completed(self, results):
        """Handle simulation completion."""
        self.current_results = results
        self.simulation_running = False
        self.run_button.config(state="normal", text="Run Simulation")
        
        # Display results
        self.display_results(results)
        
        # Generate plots if requested
        if self.generate_plots_var.get():
            try:
                self.visualizer.output_dir = Path(self.output_dir_var.get())
                plot_files = self.visualizer.save_all_plots(results, "gui_simulation")
                
                plot_info = "\\nGenerated plots:\\n"
                for plot_type, filepath in plot_files.items():
                    plot_info += f"• {plot_type}: {filepath}\\n"
                
                self.results_text.insert(tk.END, plot_info)
                
            except Exception as e:
                self.results_text.insert(tk.END, f"\\nError generating plots: {e}\\n")
        
        # Switch to results tab
        self.notebook.select(2)  # Results tab
        
        messagebox.showinfo("Success", "Simulation completed successfully!")
    
    def simulation_error(self, error_msg):
        """Handle simulation error."""
        self.simulation_running = False
        self.run_button.config(state="normal", text="Run Simulation")
        messagebox.showerror("Simulation Error", f"Simulation failed: {error_msg}")
    
    def display_results(self, results):
        """Display simulation results in the results tab."""
        self.results_text.delete(1.0, tk.END)
        
        report = self.simulator.get_simulation_report(results)
        self.results_text.insert(tk.END, report)
    
    def save_parameters(self):
        """Save current simulation parameters to file."""
        filename = filedialog.asksaveasfilename(
            title="Save Parameters",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                params = {
                    'source': self.source_var.get(),
                    'material': self.material_var.get(),
                    'activity': float(self.activity_var.get()),
                    'distance': float(self.distance_var.get()),
                    'time': float(self.time_var.get()),
                    'geometry': self.geometry_var.get(),
                    'geometry_size': float(self.geometry_size_var.get()),
                    'temperature': self.temperature_var.get() or None,
                    'humidity': self.humidity_var.get() or None
                }
                
                with open(filename, 'w') as f:
                    json.dump(params, f, indent=2)
                
                messagebox.showinfo("Success", f"Parameters saved to {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save parameters: {e}")
    
    def load_parameters(self):
        """Load simulation parameters from file."""
        filename = filedialog.askopenfilename(
            title="Load Parameters",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    params = json.load(f)
                
                # Set GUI variables
                self.source_var.set(params.get('source', 'Co-60'))
                self.material_var.set(params.get('material', 'wheat'))
                self.activity_var.set(str(params.get('activity', 1000)))
                self.distance_var.set(str(params.get('distance', 50)))
                self.time_var.set(str(params.get('time', 2.0)))
                self.geometry_var.set(params.get('geometry', 'sphere'))
                self.geometry_size_var.set(str(params.get('geometry_size', 1.0)))
                self.temperature_var.set(str(params.get('temperature', '') or ''))
                self.humidity_var.set(str(params.get('humidity', '') or ''))
                
                messagebox.showinfo("Success", f"Parameters loaded from {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load parameters: {e}")
    
    def browse_data_file(self):
        """Browse for experimental data file."""
        filename = filedialog.askopenfilename(
            title="Select Experimental Data File",
            filetypes=[
                ("CSV files", "*.csv"),
                ("JSON files", "*.json"),
                ("Excel files", "*.xlsx"),
                ("YAML files", "*.yaml *.yml"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            self.data_file_var.set(filename)
    
    def browse_output_dir(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir_var.set(directory)
    
    def load_data(self):
        """Load experimental data file."""
        if not self.data_file_var.get():
            messagebox.showerror("Error", "Please select a data file first")
            return
        
        try:
            self.experimental_data = self.data_loader.load_data(self.data_file_var.get())
            
            self.data_text.delete(1.0, tk.END)
            self.data_text.insert(tk.END, f"Loaded {len(self.experimental_data)} experimental records\\n\\n")
            
            # Show first few records
            for i, exp in enumerate(self.experimental_data[:5]):
                self.data_text.insert(tk.END, f"Record {i+1}:\\n")
                self.data_text.insert(tk.END, f"  Sample ID: {exp.sample_id}\\n")
                self.data_text.insert(tk.END, f"  Material: {exp.material}\\n")
                self.data_text.insert(tk.END, f"  Dose: {exp.dose:.2f} Gy\\n")
                self.data_text.insert(tk.END, f"  Source: {exp.source_type}\\n\\n")
            
            if len(self.experimental_data) > 5:
                self.data_text.insert(tk.END, f"... and {len(self.experimental_data) - 5} more records\\n")
            
            messagebox.showinfo("Success", f"Loaded {len(self.experimental_data)} records")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")
    
    def validate_data(self):
        """Validate loaded experimental data."""
        if not self.experimental_data:
            messagebox.showerror("Error", "Please load data first")
            return
        
        try:
            validation = self.data_loader.validate_data(self.experimental_data)
            
            self.data_text.insert(tk.END, f"\\n{'='*50}\\n")
            self.data_text.insert(tk.END, "VALIDATION RESULTS\\n")
            self.data_text.insert(tk.END, f"{'='*50}\\n")
            self.data_text.insert(tk.END, f"Valid records: {validation.valid_records}/{validation.total_records} "
                                        f"({validation.validation_rate:.1f}%)\\n\\n")
            
            if validation.errors:
                self.data_text.insert(tk.END, f"Errors ({len(validation.errors)}):  \\n")
                for error in validation.errors[:10]:  # Show first 10 errors
                    self.data_text.insert(tk.END, f"  • {error}\\n")
                if len(validation.errors) > 10:
                    self.data_text.insert(tk.END, f"  ... and {len(validation.errors) - 10} more errors\\n")
                self.data_text.insert(tk.END, "\\n")
            
            if validation.warnings:
                self.data_text.insert(tk.END, f"Warnings ({len(validation.warnings)}): \\n")
                for warning in validation.warnings[:10]:  # Show first 10 warnings
                    self.data_text.insert(tk.END, f"  • {warning}\\n")
                if len(validation.warnings) > 10:
                    self.data_text.insert(tk.END, f"  ... and {len(validation.warnings) - 10} more warnings\\n")
            
        except Exception as e:
            messagebox.showerror("Error", f"Validation failed: {e}")
    
    def generate_summary(self):
        """Generate summary statistics for loaded data."""
        if not self.experimental_data:
            messagebox.showerror("Error", "Please load data first")
            return
        
        try:
            summary = self.data_loader.get_summary_statistics(self.experimental_data)
            
            self.data_text.insert(tk.END, f"\\n{'='*50}\\n")
            self.data_text.insert(tk.END, "DATA SUMMARY\\n")
            self.data_text.insert(tk.END, f"{'='*50}\\n")
            self.data_text.insert(tk.END, f"Total records: {summary['total_records']}\\n\\n")
            
            # Dose statistics
            dose_stats = summary['dose_statistics']
            self.data_text.insert(tk.END, "Dose Statistics (Gy):\\n")
            self.data_text.insert(tk.END, f"  Mean: {dose_stats['mean']:.2f} ± {dose_stats['std']:.2f}\\n")
            self.data_text.insert(tk.END, f"  Range: {dose_stats['min']:.2f} - {dose_stats['max']:.2f}\\n")
            self.data_text.insert(tk.END, f"  Median: {dose_stats['median']:.2f}\\n\\n")
            
            # Material distribution
            self.data_text.insert(tk.END, "Material Distribution:\\n")
            for material, count in summary['material_distribution'].items():
                self.data_text.insert(tk.END, f"  {material}: {count}\\n")
            self.data_text.insert(tk.END, "\\n")
            
            # Source distribution
            self.data_text.insert(tk.END, "Source Type Distribution:\\n")
            for source, count in summary['source_type_distribution'].items():
                self.data_text.insert(tk.END, f"  {source}: {count}\\n")
            
        except Exception as e:
            messagebox.showerror("Error", f"Summary generation failed: {e}")
    
    def compare_data(self):
        """Compare experimental data with simulations."""
        if not self.experimental_data:
            messagebox.showerror("Error", "Please load experimental data first")
            return
        
        try:
            # Run comparison in thread to avoid GUI freezing
            def comparison_thread():
                try:
                    comparison = self.simulator.compare_with_experimental(self.experimental_data)
                    self.root.after(0, lambda: self.comparison_completed(comparison))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Comparison failed: {e}"))
            
            threading.Thread(target=comparison_thread, daemon=True).start()
            messagebox.showinfo("Info", "Running comparison simulations... This may take a while.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Comparison failed: {e}")
    
    def comparison_completed(self, comparison):
        """Handle comparison completion."""
        self.data_text.insert(tk.END, f"\\n{'='*50}\\n")
        self.data_text.insert(tk.END, "EXPERIMENTAL vs SIMULATION COMPARISON\\n")
        self.data_text.insert(tk.END, f"{'='*50}\\n")
        self.data_text.insert(tk.END, f"Correlation coefficient: {comparison.correlation_coefficient:.3f}\\n")
        self.data_text.insert(tk.END, f"Mean absolute error: {comparison.mean_absolute_error:.2f} Gy\\n")
        self.data_text.insert(tk.END, f"Relative error: {comparison.relative_error:.1f}%\\n")
        self.data_text.insert(tk.END, f"Number of comparisons: {comparison.statistics['n_comparisons']}\\n")
        
        try:
            # Generate comparison plot
            plot_path = Path(self.output_dir_var.get()) / "experimental_vs_simulation.png"
            self.visualizer.plot_experimental_comparison(comparison, str(plot_path))
            self.data_text.insert(tk.END, f"\\nComparison plot saved to: {plot_path}\\n")
        except Exception as e:
            self.data_text.insert(tk.END, f"\\nError generating comparison plot: {e}\\n")
        
        messagebox.showinfo("Success", "Comparison completed!")
    
    def save_results(self):
        """Save current simulation results."""
        if not self.current_results:
            messagebox.showerror("Error", "No results to save")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Results",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    output_data = {
                        'parameters': {
                            'source': self.current_results.parameters.source.value,
                            'material': self.current_results.parameters.material.name,
                            'activity': self.current_results.parameters.source_activity,
                            'distance': self.current_results.parameters.source_distance,
                            'exposure_time': self.current_results.parameters.exposure_time,
                        },
                        'results': self.current_results.get_summary()
                    }
                    
                    with open(filename, 'w') as f:
                        json.dump(output_data, f, indent=2)
                else:
                    # Save as text report
                    report = self.simulator.get_simulation_report(self.current_results)
                    with open(filename, 'w') as f:
                        f.write(report)
                
                messagebox.showinfo("Success", f"Results saved to {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save results: {e}")
    
    def generate_report(self):
        """Generate and display detailed report."""
        if not self.current_results:
            messagebox.showerror("Error", "No results available")
            return
        
        report = self.simulator.get_simulation_report(self.current_results)
        
        # Create new window for report
        report_window = tk.Toplevel(self.root)
        report_window.title("Simulation Report")
        report_window.geometry("600x500")
        
        text_widget = scrolledtext.ScrolledText(report_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert(tk.END, report)
        text_widget.config(state=tk.DISABLED)
    
    def clear_results(self):
        """Clear the results display."""
        self.results_text.delete(1.0, tk.END)
        self.current_results = None
    
    def on_closing(self):
        """Handle application closing."""
        if self.simulation_running:
            if messagebox.askokcancel("Quit", "Simulation is running. Are you sure you want to quit?"):
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """Main entry point for the GUI application."""
    root = tk.Tk()
    app = SimulationGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()