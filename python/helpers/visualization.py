"""
Visualization Helper

This module provides advanced visualization capabilities using Plotly for
interactive charts and graphs within Agent Zero.

Features:
- Interactive charts with Plotly
- Support for various chart types (line, bar, scatter, pie, etc.)
- Time series visualization
- Statistical visualizations
- Export to HTML, PNG, SVG, and JSON
- Integration with DuckDB analysis results
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
import tempfile

from python.helpers.print_style import PrintStyle
from python.helpers import files


@dataclass
class VisualizationConfig:
    """Configuration for visualization output."""
    default_template: str = "plotly_white"  # plotly, plotly_white, plotly_dark, ggplot2, seaborn, etc.
    default_width: int = 800
    default_height: int = 600
    output_dir: str = ""  # Will use tmp if empty
    interactive: bool = True  # Generate interactive HTML
    
    @classmethod
    def from_env(cls) -> "VisualizationConfig":
        """Create config from environment variables."""
        return cls(
            default_template=os.getenv("VIZ_TEMPLATE", "plotly_white"),
            default_width=int(os.getenv("VIZ_WIDTH", "800")),
            default_height=int(os.getenv("VIZ_HEIGHT", "600")),
            output_dir=os.getenv("VIZ_OUTPUT_DIR", ""),
            interactive=os.getenv("VIZ_INTERACTIVE", "true").lower() == "true",
        )


class VisualizationHelper:
    """
    Visualization helper using Plotly for creating interactive charts and graphs.
    
    This class provides methods for creating various types of visualizations
    from data analysis results.
    """
    
    def __init__(self, config: Optional[VisualizationConfig] = None):
        """Initialize visualization helper."""
        self.config = config or VisualizationConfig.from_env()
        self._plotly_available = False
        self._kaleido_available = False
        self._check_dependencies()
        
    def _check_dependencies(self) -> None:
        """Check if required dependencies are available."""
        try:
            import plotly
            self._plotly_available = True
        except ImportError:
            PrintStyle.warning(
                "Plotly not installed. Install with: pip install plotly"
            )
            
        try:
            import kaleido
            self._kaleido_available = True
        except ImportError:
            PrintStyle.warning(
                "Kaleido not installed (needed for static exports). "
                "Install with: pip install kaleido"
            )
    
    def _get_output_path(self, filename: str) -> str:
        """Get the full output path for a file."""
        if self.config.output_dir:
            output_dir = self.config.output_dir
        else:
            output_dir = files.get_abs_path("tmp", "visualizations")
            
        os.makedirs(output_dir, exist_ok=True)
        return os.path.join(output_dir, filename)
    
    # ========== Line Charts ==========
    
    def line_chart(
        self,
        data: List[Dict[str, Any]],
        x: str,
        y: Union[str, List[str]],
        title: str = "Line Chart",
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        color: Optional[str] = None,
        markers: bool = True,
        **kwargs,
    ) -> Optional[Any]:
        """
        Create a line chart.
        
        Args:
            data: List of data points as dictionaries
            x: Column name for x-axis
            y: Column name(s) for y-axis (string or list for multiple lines)
            title: Chart title
            x_label: X-axis label
            y_label: Y-axis label
            color: Column for color grouping
            markers: Show markers on data points
            **kwargs: Additional Plotly options
            
        Returns:
            Plotly figure object
        """
        if not self._plotly_available:
            return None
            
        try:
            import plotly.express as px
            import pandas as pd
            
            df = pd.DataFrame(data)
            
            if isinstance(y, list):
                # Multiple y columns - reshape for plotting
                fig = px.line(
                    df,
                    x=x,
                    y=y,
                    title=title,
                    markers=markers,
                    template=self.config.default_template,
                    **kwargs,
                )
            else:
                fig = px.line(
                    df,
                    x=x,
                    y=y,
                    color=color,
                    title=title,
                    markers=markers,
                    template=self.config.default_template,
                    **kwargs,
                )
            
            if x_label:
                fig.update_xaxes(title_text=x_label)
            if y_label:
                fig.update_yaxes(title_text=y_label)
                
            return fig
        except Exception as e:
            PrintStyle.error(f"Failed to create line chart: {e}")
            return None
    
    # ========== Bar Charts ==========
    
    def bar_chart(
        self,
        data: List[Dict[str, Any]],
        x: str,
        y: str,
        title: str = "Bar Chart",
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        color: Optional[str] = None,
        orientation: str = "v",  # 'v' for vertical, 'h' for horizontal
        barmode: str = "group",  # 'group', 'stack', 'relative'
        **kwargs,
    ) -> Optional[Any]:
        """
        Create a bar chart.
        
        Args:
            data: List of data points
            x: Column for x-axis (categories)
            y: Column for y-axis (values)
            title: Chart title
            color: Column for color grouping
            orientation: 'v' for vertical, 'h' for horizontal
            barmode: 'group', 'stack', or 'relative'
        """
        if not self._plotly_available:
            return None
            
        try:
            import plotly.express as px
            import pandas as pd
            
            df = pd.DataFrame(data)
            
            fig = px.bar(
                df,
                x=x,
                y=y,
                color=color,
                title=title,
                orientation=orientation,
                barmode=barmode,
                template=self.config.default_template,
                **kwargs,
            )
            
            if x_label:
                fig.update_xaxes(title_text=x_label)
            if y_label:
                fig.update_yaxes(title_text=y_label)
                
            return fig
        except Exception as e:
            PrintStyle.error(f"Failed to create bar chart: {e}")
            return None
    
    # ========== Scatter Plots ==========
    
    def scatter_plot(
        self,
        data: List[Dict[str, Any]],
        x: str,
        y: str,
        title: str = "Scatter Plot",
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        color: Optional[str] = None,
        size: Optional[str] = None,
        symbol: Optional[str] = None,
        trendline: Optional[str] = None,  # 'ols', 'lowess', etc.
        **kwargs,
    ) -> Optional[Any]:
        """
        Create a scatter plot.
        
        Args:
            data: List of data points
            x: Column for x-axis
            y: Column for y-axis
            color: Column for color encoding
            size: Column for size encoding
            symbol: Column for symbol/marker encoding
            trendline: Add trendline ('ols', 'lowess', 'expanding', 'rolling')
        """
        if not self._plotly_available:
            return None
            
        try:
            import plotly.express as px
            import pandas as pd
            
            df = pd.DataFrame(data)
            
            fig = px.scatter(
                df,
                x=x,
                y=y,
                color=color,
                size=size,
                symbol=symbol,
                trendline=trendline,
                title=title,
                template=self.config.default_template,
                **kwargs,
            )
            
            if x_label:
                fig.update_xaxes(title_text=x_label)
            if y_label:
                fig.update_yaxes(title_text=y_label)
                
            return fig
        except Exception as e:
            PrintStyle.error(f"Failed to create scatter plot: {e}")
            return None
    
    # ========== Pie Charts ==========
    
    def pie_chart(
        self,
        data: List[Dict[str, Any]],
        values: str,
        names: str,
        title: str = "Pie Chart",
        hole: float = 0,  # 0 for pie, 0.3-0.5 for donut
        **kwargs,
    ) -> Optional[Any]:
        """
        Create a pie or donut chart.
        
        Args:
            data: List of data points
            values: Column for slice sizes
            names: Column for slice labels
            hole: Hole size for donut chart (0 = pie, 0.3-0.5 = donut)
        """
        if not self._plotly_available:
            return None
            
        try:
            import plotly.express as px
            import pandas as pd
            
            df = pd.DataFrame(data)
            
            fig = px.pie(
                df,
                values=values,
                names=names,
                title=title,
                hole=hole,
                template=self.config.default_template,
                **kwargs,
            )
            
            return fig
        except Exception as e:
            PrintStyle.error(f"Failed to create pie chart: {e}")
            return None
    
    # ========== Histograms ==========
    
    def histogram(
        self,
        data: List[Dict[str, Any]],
        x: str,
        title: str = "Histogram",
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        color: Optional[str] = None,
        nbins: Optional[int] = None,
        marginal: Optional[str] = None,  # 'box', 'violin', 'rug'
        **kwargs,
    ) -> Optional[Any]:
        """
        Create a histogram.
        
        Args:
            data: List of data points
            x: Column for values
            color: Column for color grouping
            nbins: Number of bins
            marginal: Marginal plot type ('box', 'violin', 'rug')
        """
        if not self._plotly_available:
            return None
            
        try:
            import plotly.express as px
            import pandas as pd
            
            df = pd.DataFrame(data)
            
            fig = px.histogram(
                df,
                x=x,
                color=color,
                nbins=nbins,
                marginal=marginal,
                title=title,
                template=self.config.default_template,
                **kwargs,
            )
            
            if x_label:
                fig.update_xaxes(title_text=x_label)
            if y_label:
                fig.update_yaxes(title_text=y_label)
                
            return fig
        except Exception as e:
            PrintStyle.error(f"Failed to create histogram: {e}")
            return None
    
    # ========== Box Plots ==========
    
    def box_plot(
        self,
        data: List[Dict[str, Any]],
        y: str,
        x: Optional[str] = None,
        title: str = "Box Plot",
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        color: Optional[str] = None,
        points: str = "outliers",  # 'outliers', 'all', 'suspectedoutliers', False
        **kwargs,
    ) -> Optional[Any]:
        """
        Create a box plot.
        
        Args:
            data: List of data points
            y: Column for values
            x: Column for categories
            color: Column for color grouping
            points: Show points ('outliers', 'all', 'suspectedoutliers', False)
        """
        if not self._plotly_available:
            return None
            
        try:
            import plotly.express as px
            import pandas as pd
            
            df = pd.DataFrame(data)
            
            fig = px.box(
                df,
                x=x,
                y=y,
                color=color,
                points=points,
                title=title,
                template=self.config.default_template,
                **kwargs,
            )
            
            if x_label:
                fig.update_xaxes(title_text=x_label)
            if y_label:
                fig.update_yaxes(title_text=y_label)
                
            return fig
        except Exception as e:
            PrintStyle.error(f"Failed to create box plot: {e}")
            return None
    
    # ========== Heatmaps ==========
    
    def heatmap(
        self,
        data: List[Dict[str, Any]],
        x: str,
        y: str,
        z: str,
        title: str = "Heatmap",
        color_scale: str = "Viridis",
        **kwargs,
    ) -> Optional[Any]:
        """
        Create a heatmap.
        
        Args:
            data: List of data points
            x: Column for x-axis
            y: Column for y-axis
            z: Column for color values
            color_scale: Color scale name
        """
        if not self._plotly_available:
            return None
            
        try:
            import plotly.express as px
            import pandas as pd
            
            df = pd.DataFrame(data)
            
            # Pivot data for heatmap
            pivot_df = df.pivot(index=y, columns=x, values=z)
            
            import plotly.graph_objects as go
            
            fig = go.Figure(data=go.Heatmap(
                z=pivot_df.values,
                x=pivot_df.columns.tolist(),
                y=pivot_df.index.tolist(),
                colorscale=color_scale,
            ))
            
            fig.update_layout(
                title=title,
                template=self.config.default_template,
            )
            
            return fig
        except Exception as e:
            PrintStyle.error(f"Failed to create heatmap: {e}")
            return None
    
    # ========== Time Series ==========
    
    def time_series(
        self,
        data: List[Dict[str, Any]],
        x: str,
        y: Union[str, List[str]],
        title: str = "Time Series",
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        range_slider: bool = True,
        **kwargs,
    ) -> Optional[Any]:
        """
        Create a time series chart with range slider.
        
        Args:
            data: List of data points with timestamp column
            x: Column for time axis
            y: Column(s) for values
            range_slider: Show range slider for zooming
        """
        if not self._plotly_available:
            return None
            
        try:
            import plotly.express as px
            import pandas as pd
            
            df = pd.DataFrame(data)
            
            fig = px.line(
                df,
                x=x,
                y=y,
                title=title,
                template=self.config.default_template,
                **kwargs,
            )
            
            if range_slider:
                fig.update_xaxes(rangeslider_visible=True)
                
            if x_label:
                fig.update_xaxes(title_text=x_label)
            if y_label:
                fig.update_yaxes(title_text=y_label)
                
            return fig
        except Exception as e:
            PrintStyle.error(f"Failed to create time series: {e}")
            return None
    
    # ========== Geospatial ==========
    
    def scatter_map(
        self,
        data: List[Dict[str, Any]],
        lat: str,
        lon: str,
        title: str = "Scatter Map",
        color: Optional[str] = None,
        size: Optional[str] = None,
        hover_name: Optional[str] = None,
        mapbox_style: str = "open-street-map",
        zoom: int = 3,
        **kwargs,
    ) -> Optional[Any]:
        """
        Create a scatter plot on a map.
        
        Args:
            data: List of data points with lat/lon
            lat: Column for latitude
            lon: Column for longitude
            color: Column for color encoding
            size: Column for size encoding
            mapbox_style: Map style (open-street-map, carto-positron, etc.)
            zoom: Initial zoom level
        """
        if not self._plotly_available:
            return None
            
        try:
            import plotly.express as px
            import pandas as pd
            
            df = pd.DataFrame(data)
            
            fig = px.scatter_mapbox(
                df,
                lat=lat,
                lon=lon,
                color=color,
                size=size,
                hover_name=hover_name,
                title=title,
                mapbox_style=mapbox_style,
                zoom=zoom,
                **kwargs,
            )
            
            return fig
        except Exception as e:
            PrintStyle.error(f"Failed to create scatter map: {e}")
            return None
    
    def choropleth_map(
        self,
        data: List[Dict[str, Any]],
        locations: str,
        color: str,
        title: str = "Choropleth Map",
        location_mode: str = "ISO-3",  # 'ISO-3', 'USA-states', 'country names'
        color_scale: str = "Viridis",
        **kwargs,
    ) -> Optional[Any]:
        """
        Create a choropleth (filled) map.
        
        Args:
            data: List of data points with location codes
            locations: Column for location identifiers
            color: Column for fill color values
            location_mode: How locations are identified
            color_scale: Color scale name
        """
        if not self._plotly_available:
            return None
            
        try:
            import plotly.express as px
            import pandas as pd
            
            df = pd.DataFrame(data)
            
            fig = px.choropleth(
                df,
                locations=locations,
                color=color,
                locationmode=location_mode,
                color_continuous_scale=color_scale,
                title=title,
                **kwargs,
            )
            
            return fig
        except Exception as e:
            PrintStyle.error(f"Failed to create choropleth map: {e}")
            return None
    
    # ========== Statistical ==========
    
    def correlation_matrix(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        title: str = "Correlation Matrix",
        color_scale: str = "RdBu",
        **kwargs,
    ) -> Optional[Any]:
        """
        Create a correlation matrix heatmap.
        
        Args:
            data: List of data points
            columns: Columns to include (None = all numeric)
            color_scale: Color scale name
        """
        if not self._plotly_available:
            return None
            
        try:
            import plotly.figure_factory as ff
            import pandas as pd
            import numpy as np
            
            df = pd.DataFrame(data)
            
            if columns:
                df = df[columns]
            else:
                df = df.select_dtypes(include=[np.number])
            
            corr_matrix = df.corr()
            
            import plotly.graph_objects as go
            
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns.tolist(),
                y=corr_matrix.columns.tolist(),
                colorscale=color_scale,
                zmin=-1,
                zmax=1,
            ))
            
            fig.update_layout(
                title=title,
                template=self.config.default_template,
            )
            
            return fig
        except Exception as e:
            PrintStyle.error(f"Failed to create correlation matrix: {e}")
            return None
    
    # ========== 3D Plots ==========
    
    def scatter_3d(
        self,
        data: List[Dict[str, Any]],
        x: str,
        y: str,
        z: str,
        title: str = "3D Scatter Plot",
        color: Optional[str] = None,
        size: Optional[str] = None,
        symbol: Optional[str] = None,
        **kwargs,
    ) -> Optional[Any]:
        """
        Create a 3D scatter plot.
        
        Args:
            data: List of data points
            x, y, z: Column names for axes
            color: Column for color encoding
            size: Column for size encoding
            symbol: Column for symbol encoding
        """
        if not self._plotly_available:
            return None
            
        try:
            import plotly.express as px
            import pandas as pd
            
            df = pd.DataFrame(data)
            
            fig = px.scatter_3d(
                df,
                x=x,
                y=y,
                z=z,
                color=color,
                size=size,
                symbol=symbol,
                title=title,
                template=self.config.default_template,
                **kwargs,
            )
            
            return fig
        except Exception as e:
            PrintStyle.error(f"Failed to create 3D scatter plot: {e}")
            return None
    
    def surface_3d(
        self,
        z_data: List[List[float]],
        title: str = "3D Surface",
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        z_label: Optional[str] = None,
        color_scale: str = "Viridis",
        **kwargs,
    ) -> Optional[Any]:
        """
        Create a 3D surface plot.
        
        Args:
            z_data: 2D array of z values
            color_scale: Color scale name
        """
        if not self._plotly_available:
            return None
            
        try:
            import plotly.graph_objects as go
            
            fig = go.Figure(data=go.Surface(
                z=z_data,
                colorscale=color_scale,
            ))
            
            fig.update_layout(
                title=title,
                template=self.config.default_template,
                scene=dict(
                    xaxis_title=x_label,
                    yaxis_title=y_label,
                    zaxis_title=z_label,
                ),
            )
            
            return fig
        except Exception as e:
            PrintStyle.error(f"Failed to create 3D surface: {e}")
            return None
    
    # ========== Subplots ==========
    
    def create_subplots(
        self,
        rows: int = 1,
        cols: int = 2,
        subplot_titles: Optional[List[str]] = None,
        shared_xaxes: bool = False,
        shared_yaxes: bool = False,
        **kwargs,
    ) -> Optional[Any]:
        """
        Create a subplot grid for combining multiple charts.
        
        Args:
            rows: Number of rows
            cols: Number of columns
            subplot_titles: Titles for each subplot
            shared_xaxes: Share x-axes
            shared_yaxes: Share y-axes
            
        Returns:
            Plotly Figure with subplot grid
        """
        if not self._plotly_available:
            return None
            
        try:
            from plotly.subplots import make_subplots
            
            fig = make_subplots(
                rows=rows,
                cols=cols,
                subplot_titles=subplot_titles,
                shared_xaxes=shared_xaxes,
                shared_yaxes=shared_yaxes,
                **kwargs,
            )
            
            fig.update_layout(template=self.config.default_template)
            
            return fig
        except Exception as e:
            PrintStyle.error(f"Failed to create subplots: {e}")
            return None
    
    # ========== Export Functions ==========
    
    def save_html(
        self,
        fig: Any,
        filename: str,
        include_plotlyjs: bool = True,
        full_html: bool = True,
    ) -> Optional[str]:
        """
        Save figure as interactive HTML.
        
        Args:
            fig: Plotly figure
            filename: Output filename
            include_plotlyjs: Include Plotly.js in HTML
            full_html: Generate full HTML document
            
        Returns:
            Path to saved file
        """
        if not self._plotly_available or fig is None:
            return None
            
        try:
            path = self._get_output_path(filename)
            fig.write_html(
                path,
                include_plotlyjs=include_plotlyjs,
                full_html=full_html,
            )
            PrintStyle.standard(f"Saved HTML visualization: {path}")
            return path
        except Exception as e:
            PrintStyle.error(f"Failed to save HTML: {e}")
            return None
    
    def save_image(
        self,
        fig: Any,
        filename: str,
        format: str = "png",  # 'png', 'jpeg', 'webp', 'svg', 'pdf'
        width: Optional[int] = None,
        height: Optional[int] = None,
        scale: float = 2,
    ) -> Optional[str]:
        """
        Save figure as static image.
        
        Args:
            fig: Plotly figure
            filename: Output filename
            format: Image format
            width: Image width
            height: Image height
            scale: Scale factor
            
        Returns:
            Path to saved file
        """
        if not self._plotly_available or fig is None:
            return None
            
        if not self._kaleido_available:
            PrintStyle.warning("Kaleido not available. Cannot export static images.")
            return None
            
        try:
            path = self._get_output_path(filename)
            fig.write_image(
                path,
                format=format,
                width=width or self.config.default_width,
                height=height or self.config.default_height,
                scale=scale,
            )
            PrintStyle.standard(f"Saved image visualization: {path}")
            return path
        except Exception as e:
            PrintStyle.error(f"Failed to save image: {e}")
            return None
    
    def to_json(self, fig: Any) -> Optional[str]:
        """Convert figure to JSON string."""
        if not self._plotly_available or fig is None:
            return None
            
        try:
            return fig.to_json()
        except Exception as e:
            PrintStyle.error(f"Failed to convert to JSON: {e}")
            return None
    
    def from_json(self, json_str: str) -> Optional[Any]:
        """Create figure from JSON string."""
        if not self._plotly_available:
            return None
            
        try:
            import plotly.io as pio
            return pio.from_json(json_str)
        except Exception as e:
            PrintStyle.error(f"Failed to create from JSON: {e}")
            return None
    
    def show(self, fig: Any) -> None:
        """Display figure (in notebook or opens browser)."""
        if fig is not None:
            try:
                fig.show()
            except Exception as e:
                PrintStyle.error(f"Failed to show figure: {e}")


# Helper function for agent integration
def get_visualization_helper(
    template: str = "plotly_white",
    output_dir: Optional[str] = None,
) -> VisualizationHelper:
    """
    Get a configured visualization helper instance.
    
    Args:
        template: Plotly template name
        output_dir: Directory for saving outputs
        
    Returns:
        Configured VisualizationHelper instance
    """
    config = VisualizationConfig.from_env()
    config.default_template = template
    if output_dir:
        config.output_dir = output_dir
        
    return VisualizationHelper(config)
