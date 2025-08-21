"""
Visualization module for dose distribution and experimental comparison.

This module provides 2D and 3D visualization capabilities for dose distribution,
experimental data analysis, and simulation results comparison.
"""

import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import List, Tuple, Dict, Any, Optional
import logging
from pathlib import Path

from ..core.simulator import SimulationResults, ComparisonResults
from ..data.loader import ExperimentalData

# Configure logging
logger = logging.getLogger(__name__)

# Set matplotlib backend for headless environments
plt.switch_backend('Agg')

# Configure plotting style
plt.style.use('default')

# Try to import seaborn, fall back gracefully if not available
try:
    import seaborn as sns
    sns.set_palette("viridis")
except ImportError:
    logger.warning("Seaborn not available, using basic matplotlib styling")
    sns = None


class DoseVisualizer:
    """
    Main class for visualizing irradiation simulation results.
    
    Provides comprehensive plotting capabilities for dose distributions,
    experimental comparisons, and statistical analysis.
    """
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the visualizer.
        
        Args:
            output_dir: Directory to save plots (optional)
        """
        self.logger = logging.getLogger(__name__ + ".DoseVisualizer")
        self.output_dir = Path(output_dir) if output_dir else Path("./plots")
        self.output_dir.mkdir(exist_ok=True)
        
        # Color schemes
        self.dose_colormap = 'plasma'
        self.comparison_colors = ['#1f77b4', '#ff7f0e']
        
    def plot_dose_distribution_2d(self, 
                                 results: SimulationResults,
                                 save_path: Optional[str] = None,
                                 show_colorbar: bool = True,
                                 contour_levels: int = 20) -> plt.Figure:
        """
        Create 2D dose distribution plot.
        
        Args:
            results: Simulation results containing dose distribution
            save_path: Path to save the plot
            show_colorbar: Whether to show colorbar
            contour_levels: Number of contour levels
            
        Returns:
            Matplotlib figure object
        """
        if results.dose_distribution is None or results.coordinates is None:
            raise ValueError("Dose distribution data not available")
        
        X, Y = results.coordinates
        dose_matrix = results.dose_distribution
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Create contour plot
        contour = ax.contourf(X, Y, dose_matrix, levels=contour_levels, 
                             cmap=self.dose_colormap)
        
        # Add contour lines
        contour_lines = ax.contour(X, Y, dose_matrix, levels=contour_levels, 
                                  colors='white', alpha=0.3, linewidths=0.5)
        
        # Colorbar
        if show_colorbar:
            cbar = plt.colorbar(contour, ax=ax)
            cbar.set_label('Dose (Gy)', fontsize=12)
        
        # Labels and title
        ax.set_xlabel('X Position (cm)', fontsize=12)
        ax.set_ylabel('Y Position (cm)', fontsize=12)
        ax.set_title(f'Dose Distribution - {results.parameters.source.value} Source\\n'
                    f'Mean Dose: {results.mean_dose:.2f} Gy, '
                    f'Uniformity: {results.dose_uniformity:.3f}', fontsize=14)
        
        # Equal aspect ratio
        ax.set_aspect('equal')
        
        # Grid
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"2D dose plot saved to {save_path}")
        
        return fig
    
    def plot_dose_distribution_3d(self, 
                                 results: SimulationResults,
                                 save_path: Optional[str] = None,
                                 surface_opacity: float = 0.8) -> go.Figure:
        """
        Create 3D dose distribution plot using Plotly.
        
        Args:
            results: Simulation results containing dose distribution
            save_path: Path to save the plot (HTML)
            surface_opacity: Opacity of the 3D surface
            
        Returns:
            Plotly figure object
        """
        if results.dose_distribution is None or results.coordinates is None:
            raise ValueError("Dose distribution data not available")
        
        X, Y = results.coordinates
        dose_matrix = results.dose_distribution
        
        # Create 3D surface plot
        fig = go.Figure(data=[go.Surface(
            x=X,
            y=Y,
            z=dose_matrix,
            colorscale='Plasma',
            opacity=surface_opacity,
            colorbar=dict(title="Dose (Gy)")
        )])
        
        fig.update_layout(
            title=f'3D Dose Distribution - {results.parameters.source.value} Source<br>'
                  f'Mean Dose: {results.mean_dose:.2f} Gy, '
                  f'Uniformity: {results.dose_uniformity:.3f}',
            scene=dict(
                xaxis_title='X Position (cm)',
                yaxis_title='Y Position (cm)',
                zaxis_title='Dose (Gy)',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            width=800,
            height=600
        )
        
        if save_path:
            fig.write_html(save_path)
            self.logger.info(f"3D dose plot saved to {save_path}")
        
        return fig
    
    def plot_experimental_comparison(self, 
                                   comparison: ComparisonResults,
                                   save_path: Optional[str] = None,
                                   show_stats: bool = True) -> plt.Figure:
        """
        Create experimental vs simulation comparison plot.
        
        Args:
            comparison: Comparison results
            save_path: Path to save the plot
            show_stats: Whether to show statistics on plot
            
        Returns:
            Matplotlib figure object
        """
        exp_doses = [exp.dose for exp in comparison.experimental_data]
        sim_doses = [res.uniform_dose for res in comparison.simulation_results]
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Scatter plot
        ax.scatter(exp_doses, sim_doses, alpha=0.6, s=60, 
                  color=self.comparison_colors[0], edgecolors='black')
        
        # Perfect agreement line
        min_dose = min(min(exp_doses), min(sim_doses))
        max_dose = max(max(exp_doses), max(sim_doses))
        ax.plot([min_dose, max_dose], [min_dose, max_dose], 
               'r--', alpha=0.8, linewidth=2, label='Perfect Agreement')
        
        # Regression line
        z = np.polyfit(exp_doses, sim_doses, 1)
        p = np.poly1d(z)
        ax.plot(exp_doses, p(exp_doses), 'g-', alpha=0.8, linewidth=2, 
               label=f'Linear Fit (y = {z[0]:.2f}x + {z[1]:.2f})')
        
        # Labels and title
        ax.set_xlabel('Experimental Dose (Gy)', fontsize=12)
        ax.set_ylabel('Simulated Dose (Gy)', fontsize=12)
        ax.set_title('Experimental vs Simulated Dose Comparison', fontsize=14)
        
        # Statistics text box
        if show_stats:
            stats_text = (f'r = {comparison.correlation_coefficient:.3f}\\n'
                         f'MAE = {comparison.mean_absolute_error:.2f} Gy\\n'
                         f'Relative Error = {comparison.relative_error:.1f}%\\n'
                         f'n = {len(exp_doses)}')
            ax.text(0.05, 0.95, stats_text, transform=ax.transAxes, 
                   fontsize=10, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Equal axes for better comparison
        ax.set_aspect('equal', adjustable='box')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Comparison plot saved to {save_path}")
        
        return fig
    
    def plot_dose_histogram(self, 
                           results: SimulationResults,
                           bins: int = 50,
                           save_path: Optional[str] = None) -> plt.Figure:
        """
        Create histogram of dose distribution.
        
        Args:
            results: Simulation results
            bins: Number of histogram bins
            save_path: Path to save the plot
            
        Returns:
            Matplotlib figure object
        """
        if results.dose_distribution is None:
            raise ValueError("Dose distribution data not available")
        
        # Extract non-zero doses
        doses = results.dose_distribution[results.dose_distribution > 0].flatten()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Histogram
        n, bins_edges, patches = ax.hist(doses, bins=bins, alpha=0.7, 
                                        color=self.comparison_colors[0], 
                                        edgecolor='black')
        
        # Statistics lines
        ax.axvline(results.mean_dose, color='red', linestyle='--', linewidth=2, 
                  label=f'Mean: {results.mean_dose:.2f} Gy')
        ax.axvline(results.min_dose, color='blue', linestyle='--', linewidth=2, 
                  label=f'Min: {results.min_dose:.2f} Gy')
        ax.axvline(results.max_dose, color='green', linestyle='--', linewidth=2, 
                  label=f'Max: {results.max_dose:.2f} Gy')
        
        # Labels and title
        ax.set_xlabel('Dose (Gy)', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title(f'Dose Distribution Histogram\\n'
                    f'Uniformity Ratio: {results.dose_uniformity:.3f}', fontsize=14)
        
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Dose histogram saved to {save_path}")
        
        return fig
    
    def plot_parameter_sensitivity(self, 
                                 parameter_name: str,
                                 parameter_values: List[float],
                                 dose_results: List[float],
                                 save_path: Optional[str] = None) -> plt.Figure:
        """
        Create parameter sensitivity analysis plot.
        
        Args:
            parameter_name: Name of the parameter
            parameter_values: List of parameter values
            dose_results: Corresponding dose results
            save_path: Path to save the plot
            
        Returns:
            Matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.plot(parameter_values, dose_results, 'o-', linewidth=2, 
               markersize=8, color=self.comparison_colors[0])
        
        ax.set_xlabel(parameter_name, fontsize=12)
        ax.set_ylabel('Dose (Gy)', fontsize=12)
        ax.set_title(f'Parameter Sensitivity Analysis: {parameter_name}', fontsize=14)
        
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Sensitivity plot saved to {save_path}")
        
        return fig
    
    def plot_experimental_data_overview(self, 
                                      data: List[ExperimentalData],
                                      save_path: Optional[str] = None) -> plt.Figure:
        """
        Create overview plots of experimental data.
        
        Args:
            data: List of experimental data
            save_path: Path to save the plot
            
        Returns:
            Matplotlib figure object
        """
        if not data:
            raise ValueError("No experimental data provided")
        
        # Extract data
        doses = [exp.dose for exp in data]
        dose_rates = [exp.dose_rate for exp in data]
        exposure_times = [exp.exposure_time for exp in data]
        materials = [exp.material for exp in data]
        sources = [exp.source_type for exp in data]
        
        # Create subplots
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        
        # Dose distribution
        axes[0, 0].hist(doses, bins=20, alpha=0.7, color=self.comparison_colors[0])
        axes[0, 0].set_xlabel('Dose (Gy)')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].set_title('Dose Distribution')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Dose rate distribution
        axes[0, 1].hist(dose_rates, bins=20, alpha=0.7, color=self.comparison_colors[1])
        axes[0, 1].set_xlabel('Dose Rate (Gy/h)')
        axes[0, 1].set_ylabel('Frequency')
        axes[0, 1].set_title('Dose Rate Distribution')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Exposure time distribution
        axes[0, 2].hist(exposure_times, bins=20, alpha=0.7, color='green')
        axes[0, 2].set_xlabel('Exposure Time (h)')
        axes[0, 2].set_ylabel('Frequency')
        axes[0, 2].set_title('Exposure Time Distribution')
        axes[0, 2].grid(True, alpha=0.3)
        
        # Material distribution
        material_counts = {}
        for material in materials:
            material_counts[material] = material_counts.get(material, 0) + 1
        
        axes[1, 0].bar(material_counts.keys(), material_counts.values(), 
                      alpha=0.7, color='purple')
        axes[1, 0].set_xlabel('Material')
        axes[1, 0].set_ylabel('Count')
        axes[1, 0].set_title('Material Distribution')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Source distribution
        source_counts = {}
        for source in sources:
            source_counts[source] = source_counts.get(source, 0) + 1
        
        axes[1, 1].bar(source_counts.keys(), source_counts.values(), 
                      alpha=0.7, color='orange')
        axes[1, 1].set_xlabel('Source Type')
        axes[1, 1].set_ylabel('Count')
        axes[1, 1].set_title('Source Type Distribution')
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        # Dose vs Dose Rate scatter
        axes[1, 2].scatter(dose_rates, doses, alpha=0.6, s=60, 
                          color=self.comparison_colors[0])
        axes[1, 2].set_xlabel('Dose Rate (Gy/h)')
        axes[1, 2].set_ylabel('Dose (Gy)')
        axes[1, 2].set_title('Dose vs Dose Rate')
        axes[1, 2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            self.logger.info(f"Data overview plot saved to {save_path}")
        
        return fig
    
    def create_simulation_dashboard(self, 
                                  results: SimulationResults,
                                  save_path: Optional[str] = None) -> go.Figure:
        """
        Create interactive dashboard with multiple plots.
        
        Args:
            results: Simulation results
            save_path: Path to save HTML dashboard
            
        Returns:
            Plotly figure object
        """
        if results.dose_distribution is None or results.coordinates is None:
            raise ValueError("Dose distribution data not available")
        
        X, Y = results.coordinates
        dose_matrix = results.dose_distribution
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('2D Dose Distribution', 'Dose Profile (X-axis)', 
                           'Dose Profile (Y-axis)', 'Statistics'),
            specs=[[{"type": "heatmap"}, {"type": "scatter"}],
                   [{"type": "scatter"}, {"type": "table"}]]
        )
        
        # 2D heatmap
        fig.add_trace(
            go.Heatmap(x=X[0,:], y=Y[:,0], z=dose_matrix, 
                      colorscale='Plasma', name='Dose'),
            row=1, col=1
        )
        
        # X-axis profile (center)
        center_y = dose_matrix.shape[0] // 2
        fig.add_trace(
            go.Scatter(x=X[center_y,:], y=dose_matrix[center_y,:], 
                      mode='lines', name='X Profile'),
            row=1, col=2
        )
        
        # Y-axis profile (center)
        center_x = dose_matrix.shape[1] // 2
        fig.add_trace(
            go.Scatter(x=Y[:,center_x], y=dose_matrix[:,center_x], 
                      mode='lines', name='Y Profile'),
            row=2, col=1
        )
        
        # Statistics table
        stats_data = [
            ['Parameter', 'Value'],
            ['Mean Dose (Gy)', f'{results.mean_dose:.2f}'],
            ['Max Dose (Gy)', f'{results.max_dose:.2f}'],
            ['Min Dose (Gy)', f'{results.min_dose:.2f}'],
            ['Uniformity Ratio', f'{results.dose_uniformity:.3f}'],
            ['Source', results.parameters.source.value],
            ['Exposure Time (h)', f'{results.parameters.exposure_time:.2f}'],
            ['Material', results.parameters.material.name]
        ]
        
        fig.add_trace(
            go.Table(
                header=dict(values=stats_data[0],
                           fill_color='paleturquoise',
                           align='left'),
                cells=dict(values=list(zip(*stats_data[1:])),
                          fill_color='lavender',
                          align='left')
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text=f"Irradiation Simulation Dashboard - {results.parameters.source.value}",
            height=800,
            showlegend=False
        )
        
        if save_path:
            fig.write_html(save_path)
            self.logger.info(f"Dashboard saved to {save_path}")
        
        return fig
    
    def save_all_plots(self, 
                      results: SimulationResults,
                      prefix: str = "simulation") -> Dict[str, str]:
        """
        Save all visualization plots for a simulation.
        
        Args:
            results: Simulation results
            prefix: Filename prefix
            
        Returns:
            Dictionary of plot types and their file paths
        """
        saved_files = {}
        
        try:
            # 2D dose distribution
            path_2d = self.output_dir / f"{prefix}_dose_2d.png"
            self.plot_dose_distribution_2d(results, save_path=str(path_2d))
            saved_files['dose_2d'] = str(path_2d)
        except Exception as e:
            self.logger.error(f"Error saving 2D plot: {e}")
        
        try:
            # 3D dose distribution
            path_3d = self.output_dir / f"{prefix}_dose_3d.html"
            self.plot_dose_distribution_3d(results, save_path=str(path_3d))
            saved_files['dose_3d'] = str(path_3d)
        except Exception as e:
            self.logger.error(f"Error saving 3D plot: {e}")
        
        try:
            # Dose histogram
            path_hist = self.output_dir / f"{prefix}_histogram.png"
            self.plot_dose_histogram(results, save_path=str(path_hist))
            saved_files['histogram'] = str(path_hist)
        except Exception as e:
            self.logger.error(f"Error saving histogram: {e}")
        
        try:
            # Dashboard
            path_dashboard = self.output_dir / f"{prefix}_dashboard.html"
            self.create_simulation_dashboard(results, save_path=str(path_dashboard))
            saved_files['dashboard'] = str(path_dashboard)
        except Exception as e:
            self.logger.error(f"Error saving dashboard: {e}")
        
        self.logger.info(f"Saved {len(saved_files)} plots with prefix '{prefix}'")
        return saved_files