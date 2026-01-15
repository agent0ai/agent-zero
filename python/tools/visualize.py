"""
Visualization Tool

This tool provides advanced visualization capabilities using Plotly
for creating interactive charts, graphs, and maps.
"""

import json
import os
from typing import Any, Dict, List, Optional

from python.helpers.tool import Tool, Response
from python.helpers.visualization import (
    VisualizationHelper,
    get_visualization_helper,
)
from python.helpers.print_style import PrintStyle
from python.helpers import files


class Visualize(Tool):
    """
    Visualization tool for creating charts, graphs, and maps.
    
    Methods:
        line: Create a line chart
        bar: Create a bar chart
        scatter: Create a scatter plot
        pie: Create a pie/donut chart
        histogram: Create a histogram
        box: Create a box plot
        heatmap: Create a heatmap
        time_series: Create a time series chart
        scatter_map: Create a geographic scatter map
        choropleth: Create a choropleth map
        correlation: Create a correlation matrix
        scatter_3d: Create a 3D scatter plot
        surface_3d: Create a 3D surface plot
        save: Save a visualization to file
    """
    
    async def execute(self, **kwargs) -> Response:
        """Execute the visualization tool based on method."""
        method = self.method or kwargs.get("method", "line")
        
        # Get visualization helper
        template = kwargs.get("template", "plotly_white")
        output_dir = kwargs.get("output_dir", files.get_abs_path("tmp", "visualizations"))
        self._viz = get_visualization_helper(template, output_dir)
        
        try:
            if method == "line":
                return await self._create_line_chart(**kwargs)
            elif method == "bar":
                return await self._create_bar_chart(**kwargs)
            elif method == "scatter":
                return await self._create_scatter_plot(**kwargs)
            elif method == "pie":
                return await self._create_pie_chart(**kwargs)
            elif method == "histogram":
                return await self._create_histogram(**kwargs)
            elif method == "box":
                return await self._create_box_plot(**kwargs)
            elif method == "heatmap":
                return await self._create_heatmap(**kwargs)
            elif method == "time_series":
                return await self._create_time_series(**kwargs)
            elif method == "scatter_map":
                return await self._create_scatter_map(**kwargs)
            elif method == "choropleth":
                return await self._create_choropleth(**kwargs)
            elif method == "correlation":
                return await self._create_correlation(**kwargs)
            elif method == "scatter_3d":
                return await self._create_scatter_3d(**kwargs)
            elif method == "surface_3d":
                return await self._create_surface_3d(**kwargs)
            else:
                return Response(
                    message=f"Unknown method: {method}. Available methods: line, bar, scatter, pie, histogram, box, heatmap, time_series, scatter_map, choropleth, correlation, scatter_3d, surface_3d",
                    break_loop=False
                )
        except Exception as e:
            return Response(
                message=f"Visualization error: {str(e)}",
                break_loop=False
            )
    
    def _save_figure(self, fig, filename: str, format: str = "html", **kwargs) -> str:
        """Save figure and return path."""
        if fig is None:
            return ""
        
        if format == "html":
            path = self._viz.save_html(fig, f"{filename}.html")
        else:
            path = self._viz.save_image(fig, f"{filename}.{format}", format=format, **kwargs)
        
        return path or ""
    
    async def _create_line_chart(self, **kwargs) -> Response:
        """Create a line chart."""
        data = kwargs.get("data", [])
        x = kwargs.get("x", "")
        y = kwargs.get("y", "")
        title = kwargs.get("title", "Line Chart")
        x_label = kwargs.get("x_label", None)
        y_label = kwargs.get("y_label", None)
        color = kwargs.get("color", None)
        markers = kwargs.get("markers", True)
        filename = kwargs.get("filename", "line_chart")
        output_format = kwargs.get("format", "html")
        
        if not data:
            return Response(message="No data provided", break_loop=False)
        if not x or not y:
            return Response(message="Both x and y columns are required", break_loop=False)
        
        fig = self._viz.line_chart(
            data=data,
            x=x,
            y=y,
            title=title,
            x_label=x_label,
            y_label=y_label,
            color=color,
            markers=markers
        )
        
        if fig is None:
            return Response(message="Failed to create line chart (Plotly not available)", break_loop=False)
        
        path = self._save_figure(fig, filename, output_format)
        
        return Response(
            message=f"Line chart created successfully.\nSaved to: {path}",
            break_loop=False
        )
    
    async def _create_bar_chart(self, **kwargs) -> Response:
        """Create a bar chart."""
        data = kwargs.get("data", [])
        x = kwargs.get("x", "")
        y = kwargs.get("y", "")
        title = kwargs.get("title", "Bar Chart")
        x_label = kwargs.get("x_label", None)
        y_label = kwargs.get("y_label", None)
        color = kwargs.get("color", None)
        orientation = kwargs.get("orientation", "v")
        barmode = kwargs.get("barmode", "group")
        filename = kwargs.get("filename", "bar_chart")
        output_format = kwargs.get("format", "html")
        
        if not data:
            return Response(message="No data provided", break_loop=False)
        if not x or not y:
            return Response(message="Both x and y columns are required", break_loop=False)
        
        fig = self._viz.bar_chart(
            data=data,
            x=x,
            y=y,
            title=title,
            x_label=x_label,
            y_label=y_label,
            color=color,
            orientation=orientation,
            barmode=barmode
        )
        
        if fig is None:
            return Response(message="Failed to create bar chart (Plotly not available)", break_loop=False)
        
        path = self._save_figure(fig, filename, output_format)
        
        return Response(
            message=f"Bar chart created successfully.\nSaved to: {path}",
            break_loop=False
        )
    
    async def _create_scatter_plot(self, **kwargs) -> Response:
        """Create a scatter plot."""
        data = kwargs.get("data", [])
        x = kwargs.get("x", "")
        y = kwargs.get("y", "")
        title = kwargs.get("title", "Scatter Plot")
        x_label = kwargs.get("x_label", None)
        y_label = kwargs.get("y_label", None)
        color = kwargs.get("color", None)
        size = kwargs.get("size", None)
        symbol = kwargs.get("symbol", None)
        trendline = kwargs.get("trendline", None)
        filename = kwargs.get("filename", "scatter_plot")
        output_format = kwargs.get("format", "html")
        
        if not data:
            return Response(message="No data provided", break_loop=False)
        if not x or not y:
            return Response(message="Both x and y columns are required", break_loop=False)
        
        fig = self._viz.scatter_plot(
            data=data,
            x=x,
            y=y,
            title=title,
            x_label=x_label,
            y_label=y_label,
            color=color,
            size=size,
            symbol=symbol,
            trendline=trendline
        )
        
        if fig is None:
            return Response(message="Failed to create scatter plot (Plotly not available)", break_loop=False)
        
        path = self._save_figure(fig, filename, output_format)
        
        return Response(
            message=f"Scatter plot created successfully.\nSaved to: {path}",
            break_loop=False
        )
    
    async def _create_pie_chart(self, **kwargs) -> Response:
        """Create a pie or donut chart."""
        data = kwargs.get("data", [])
        values = kwargs.get("values", "")
        names = kwargs.get("names", "")
        title = kwargs.get("title", "Pie Chart")
        hole = kwargs.get("hole", 0)
        filename = kwargs.get("filename", "pie_chart")
        output_format = kwargs.get("format", "html")
        
        if not data:
            return Response(message="No data provided", break_loop=False)
        if not values or not names:
            return Response(message="Both values and names columns are required", break_loop=False)
        
        fig = self._viz.pie_chart(
            data=data,
            values=values,
            names=names,
            title=title,
            hole=hole
        )
        
        if fig is None:
            return Response(message="Failed to create pie chart (Plotly not available)", break_loop=False)
        
        path = self._save_figure(fig, filename, output_format)
        
        chart_type = "Donut" if hole > 0 else "Pie"
        return Response(
            message=f"{chart_type} chart created successfully.\nSaved to: {path}",
            break_loop=False
        )
    
    async def _create_histogram(self, **kwargs) -> Response:
        """Create a histogram."""
        data = kwargs.get("data", [])
        x = kwargs.get("x", "")
        title = kwargs.get("title", "Histogram")
        x_label = kwargs.get("x_label", None)
        y_label = kwargs.get("y_label", None)
        color = kwargs.get("color", None)
        nbins = kwargs.get("nbins", None)
        marginal = kwargs.get("marginal", None)
        filename = kwargs.get("filename", "histogram")
        output_format = kwargs.get("format", "html")
        
        if not data:
            return Response(message="No data provided", break_loop=False)
        if not x:
            return Response(message="x column is required", break_loop=False)
        
        fig = self._viz.histogram(
            data=data,
            x=x,
            title=title,
            x_label=x_label,
            y_label=y_label,
            color=color,
            nbins=nbins,
            marginal=marginal
        )
        
        if fig is None:
            return Response(message="Failed to create histogram (Plotly not available)", break_loop=False)
        
        path = self._save_figure(fig, filename, output_format)
        
        return Response(
            message=f"Histogram created successfully.\nSaved to: {path}",
            break_loop=False
        )
    
    async def _create_box_plot(self, **kwargs) -> Response:
        """Create a box plot."""
        data = kwargs.get("data", [])
        y = kwargs.get("y", "")
        x = kwargs.get("x", None)
        title = kwargs.get("title", "Box Plot")
        x_label = kwargs.get("x_label", None)
        y_label = kwargs.get("y_label", None)
        color = kwargs.get("color", None)
        points = kwargs.get("points", "outliers")
        filename = kwargs.get("filename", "box_plot")
        output_format = kwargs.get("format", "html")
        
        if not data:
            return Response(message="No data provided", break_loop=False)
        if not y:
            return Response(message="y column is required", break_loop=False)
        
        fig = self._viz.box_plot(
            data=data,
            y=y,
            x=x,
            title=title,
            x_label=x_label,
            y_label=y_label,
            color=color,
            points=points
        )
        
        if fig is None:
            return Response(message="Failed to create box plot (Plotly not available)", break_loop=False)
        
        path = self._save_figure(fig, filename, output_format)
        
        return Response(
            message=f"Box plot created successfully.\nSaved to: {path}",
            break_loop=False
        )
    
    async def _create_heatmap(self, **kwargs) -> Response:
        """Create a heatmap."""
        data = kwargs.get("data", [])
        x = kwargs.get("x", "")
        y = kwargs.get("y", "")
        z = kwargs.get("z", "")
        title = kwargs.get("title", "Heatmap")
        color_scale = kwargs.get("color_scale", "Viridis")
        filename = kwargs.get("filename", "heatmap")
        output_format = kwargs.get("format", "html")
        
        if not data:
            return Response(message="No data provided", break_loop=False)
        if not x or not y or not z:
            return Response(message="x, y, and z columns are required", break_loop=False)
        
        fig = self._viz.heatmap(
            data=data,
            x=x,
            y=y,
            z=z,
            title=title,
            color_scale=color_scale
        )
        
        if fig is None:
            return Response(message="Failed to create heatmap (Plotly not available)", break_loop=False)
        
        path = self._save_figure(fig, filename, output_format)
        
        return Response(
            message=f"Heatmap created successfully.\nSaved to: {path}",
            break_loop=False
        )
    
    async def _create_time_series(self, **kwargs) -> Response:
        """Create a time series chart."""
        data = kwargs.get("data", [])
        x = kwargs.get("x", "")
        y = kwargs.get("y", "")
        title = kwargs.get("title", "Time Series")
        x_label = kwargs.get("x_label", None)
        y_label = kwargs.get("y_label", None)
        range_slider = kwargs.get("range_slider", True)
        filename = kwargs.get("filename", "time_series")
        output_format = kwargs.get("format", "html")
        
        if not data:
            return Response(message="No data provided", break_loop=False)
        if not x or not y:
            return Response(message="Both x (time) and y (value) columns are required", break_loop=False)
        
        fig = self._viz.time_series(
            data=data,
            x=x,
            y=y,
            title=title,
            x_label=x_label,
            y_label=y_label,
            range_slider=range_slider
        )
        
        if fig is None:
            return Response(message="Failed to create time series (Plotly not available)", break_loop=False)
        
        path = self._save_figure(fig, filename, output_format)
        
        return Response(
            message=f"Time series chart created successfully.\nSaved to: {path}",
            break_loop=False
        )
    
    async def _create_scatter_map(self, **kwargs) -> Response:
        """Create a geographic scatter map."""
        data = kwargs.get("data", [])
        lat = kwargs.get("lat", "")
        lon = kwargs.get("lon", "")
        title = kwargs.get("title", "Scatter Map")
        color = kwargs.get("color", None)
        size = kwargs.get("size", None)
        hover_name = kwargs.get("hover_name", None)
        mapbox_style = kwargs.get("mapbox_style", "open-street-map")
        zoom = kwargs.get("zoom", 3)
        filename = kwargs.get("filename", "scatter_map")
        output_format = kwargs.get("format", "html")
        
        if not data:
            return Response(message="No data provided", break_loop=False)
        if not lat or not lon:
            return Response(message="Both lat and lon columns are required", break_loop=False)
        
        fig = self._viz.scatter_map(
            data=data,
            lat=lat,
            lon=lon,
            title=title,
            color=color,
            size=size,
            hover_name=hover_name,
            mapbox_style=mapbox_style,
            zoom=zoom
        )
        
        if fig is None:
            return Response(message="Failed to create scatter map (Plotly not available)", break_loop=False)
        
        path = self._save_figure(fig, filename, output_format)
        
        return Response(
            message=f"Scatter map created successfully.\nSaved to: {path}",
            break_loop=False
        )
    
    async def _create_choropleth(self, **kwargs) -> Response:
        """Create a choropleth map."""
        data = kwargs.get("data", [])
        locations = kwargs.get("locations", "")
        color = kwargs.get("color", "")
        title = kwargs.get("title", "Choropleth Map")
        location_mode = kwargs.get("location_mode", "ISO-3")
        color_scale = kwargs.get("color_scale", "Viridis")
        filename = kwargs.get("filename", "choropleth")
        output_format = kwargs.get("format", "html")
        
        if not data:
            return Response(message="No data provided", break_loop=False)
        if not locations or not color:
            return Response(message="Both locations and color columns are required", break_loop=False)
        
        fig = self._viz.choropleth_map(
            data=data,
            locations=locations,
            color=color,
            title=title,
            location_mode=location_mode,
            color_scale=color_scale
        )
        
        if fig is None:
            return Response(message="Failed to create choropleth map (Plotly not available)", break_loop=False)
        
        path = self._save_figure(fig, filename, output_format)
        
        return Response(
            message=f"Choropleth map created successfully.\nSaved to: {path}",
            break_loop=False
        )
    
    async def _create_correlation(self, **kwargs) -> Response:
        """Create a correlation matrix."""
        data = kwargs.get("data", [])
        columns = kwargs.get("columns", None)
        title = kwargs.get("title", "Correlation Matrix")
        color_scale = kwargs.get("color_scale", "RdBu")
        filename = kwargs.get("filename", "correlation_matrix")
        output_format = kwargs.get("format", "html")
        
        if not data:
            return Response(message="No data provided", break_loop=False)
        
        fig = self._viz.correlation_matrix(
            data=data,
            columns=columns,
            title=title,
            color_scale=color_scale
        )
        
        if fig is None:
            return Response(message="Failed to create correlation matrix (Plotly not available)", break_loop=False)
        
        path = self._save_figure(fig, filename, output_format)
        
        return Response(
            message=f"Correlation matrix created successfully.\nSaved to: {path}",
            break_loop=False
        )
    
    async def _create_scatter_3d(self, **kwargs) -> Response:
        """Create a 3D scatter plot."""
        data = kwargs.get("data", [])
        x = kwargs.get("x", "")
        y = kwargs.get("y", "")
        z = kwargs.get("z", "")
        title = kwargs.get("title", "3D Scatter Plot")
        color = kwargs.get("color", None)
        size = kwargs.get("size", None)
        symbol = kwargs.get("symbol", None)
        filename = kwargs.get("filename", "scatter_3d")
        output_format = kwargs.get("format", "html")
        
        if not data:
            return Response(message="No data provided", break_loop=False)
        if not x or not y or not z:
            return Response(message="x, y, and z columns are required", break_loop=False)
        
        fig = self._viz.scatter_3d(
            data=data,
            x=x,
            y=y,
            z=z,
            title=title,
            color=color,
            size=size,
            symbol=symbol
        )
        
        if fig is None:
            return Response(message="Failed to create 3D scatter plot (Plotly not available)", break_loop=False)
        
        path = self._save_figure(fig, filename, output_format)
        
        return Response(
            message=f"3D scatter plot created successfully.\nSaved to: {path}",
            break_loop=False
        )
    
    async def _create_surface_3d(self, **kwargs) -> Response:
        """Create a 3D surface plot."""
        z_data = kwargs.get("z_data", [])
        title = kwargs.get("title", "3D Surface")
        x_label = kwargs.get("x_label", None)
        y_label = kwargs.get("y_label", None)
        z_label = kwargs.get("z_label", None)
        color_scale = kwargs.get("color_scale", "Viridis")
        filename = kwargs.get("filename", "surface_3d")
        output_format = kwargs.get("format", "html")
        
        if not z_data:
            return Response(message="No z_data (2D array) provided", break_loop=False)
        
        fig = self._viz.surface_3d(
            z_data=z_data,
            title=title,
            x_label=x_label,
            y_label=y_label,
            z_label=z_label,
            color_scale=color_scale
        )
        
        if fig is None:
            return Response(message="Failed to create 3D surface (Plotly not available)", break_loop=False)
        
        path = self._save_figure(fig, filename, output_format)
        
        return Response(
            message=f"3D surface plot created successfully.\nSaved to: {path}",
            break_loop=False
        )
