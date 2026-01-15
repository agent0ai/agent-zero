### visualize
create interactive charts and visualizations using Plotly
methods: line, bar, scatter, pie, histogram, box, heatmap, time_series, scatter_map, choropleth, correlation, scatter_3d, surface_3d
outputs to HTML files in tmp/visualizations by default
supports PNG, SVG, PDF export with kaleido

1. line chart
~~~json
{
    "thoughts": [
        "Need to visualize trend over time..."
    ],
    "headline": "Creating line chart for trend analysis",
    "tool_name": "visualize:line",
    "tool_args": {
        "data": [
            {"date": "2024-01", "sales": 100, "region": "North"},
            {"date": "2024-02", "sales": 150, "region": "North"},
            {"date": "2024-01", "sales": 80, "region": "South"},
            {"date": "2024-02", "sales": 120, "region": "South"}
        ],
        "x": "date",
        "y": "sales",
        "color": "region",
        "title": "Sales Trend by Region",
        "markers": true,
        "filename": "sales_trend"
    }
}
~~~

2. bar chart
~~~json
{
    "thoughts": [
        "Need to compare values across categories..."
    ],
    "headline": "Creating bar chart for comparison",
    "tool_name": "visualize:bar",
    "tool_args": {
        "data": [
            {"category": "A", "value": 100},
            {"category": "B", "value": 150},
            {"category": "C", "value": 80}
        ],
        "x": "category",
        "y": "value",
        "title": "Category Comparison",
        "barmode": "group",
        "filename": "category_comparison"
    }
}
~~~

3. scatter plot with trendline
~~~json
{
    "thoughts": [
        "Need to visualize relationship between variables..."
    ],
    "headline": "Creating scatter plot with trendline",
    "tool_name": "visualize:scatter",
    "tool_args": {
        "data": [
            {"x": 1, "y": 2, "size": 10},
            {"x": 2, "y": 4, "size": 20},
            {"x": 3, "y": 5, "size": 15}
        ],
        "x": "x",
        "y": "y",
        "size": "size",
        "trendline": "ols",
        "title": "Correlation Analysis",
        "filename": "scatter_analysis"
    }
}
~~~

4. pie/donut chart
~~~json
{
    "thoughts": [
        "Need to show composition..."
    ],
    "headline": "Creating pie chart for composition",
    "tool_name": "visualize:pie",
    "tool_args": {
        "data": [
            {"category": "A", "value": 40},
            {"category": "B", "value": 35},
            {"category": "C", "value": 25}
        ],
        "values": "value",
        "names": "category",
        "title": "Market Share",
        "hole": 0.4,
        "filename": "market_share"
    }
}
~~~

5. histogram
~~~json
{
    "thoughts": [
        "Need to show distribution..."
    ],
    "headline": "Creating histogram for distribution",
    "tool_name": "visualize:histogram",
    "tool_args": {
        "data": [{"value": 10}, {"value": 15}, {"value": 12}, ...],
        "x": "value",
        "nbins": 20,
        "marginal": "box",
        "title": "Value Distribution",
        "filename": "distribution"
    }
}
~~~

6. box plot
~~~json
{
    "thoughts": [
        "Need to compare distributions across groups..."
    ],
    "headline": "Creating box plot",
    "tool_name": "visualize:box",
    "tool_args": {
        "data": [
            {"group": "A", "value": 10},
            {"group": "A", "value": 12},
            {"group": "B", "value": 15}
        ],
        "x": "group",
        "y": "value",
        "title": "Distribution by Group",
        "points": "all",
        "filename": "boxplot"
    }
}
~~~

7. heatmap
~~~json
{
    "thoughts": [
        "Need to show matrix values as colors..."
    ],
    "headline": "Creating heatmap visualization",
    "tool_name": "visualize:heatmap",
    "tool_args": {
        "data": [
            {"row": "A", "col": "X", "value": 10},
            {"row": "A", "col": "Y", "value": 20},
            {"row": "B", "col": "X", "value": 15}
        ],
        "x": "col",
        "y": "row",
        "z": "value",
        "color_scale": "Viridis",
        "title": "Correlation Heatmap",
        "filename": "heatmap"
    }
}
~~~

8. time series with range slider
~~~json
{
    "thoughts": [
        "Need interactive time series with zoom..."
    ],
    "headline": "Creating time series chart",
    "tool_name": "visualize:time_series",
    "tool_args": {
        "data": [
            {"timestamp": "2024-01-01", "value": 100},
            {"timestamp": "2024-01-02", "value": 110}
        ],
        "x": "timestamp",
        "y": "value",
        "range_slider": true,
        "title": "Time Series Analysis",
        "filename": "timeseries"
    }
}
~~~

9. geographic scatter map
~~~json
{
    "thoughts": [
        "Need to plot locations on map..."
    ],
    "headline": "Creating geographic scatter map",
    "tool_name": "visualize:scatter_map",
    "tool_args": {
        "data": [
            {"lat": 37.7749, "lon": -122.4194, "city": "SF", "pop": 800000},
            {"lat": 34.0522, "lon": -118.2437, "city": "LA", "pop": 4000000}
        ],
        "lat": "lat",
        "lon": "lon",
        "color": "pop",
        "hover_name": "city",
        "title": "City Locations",
        "zoom": 5,
        "filename": "city_map"
    }
}
~~~

10. correlation matrix
~~~json
{
    "thoughts": [
        "Need to visualize correlations between variables..."
    ],
    "headline": "Creating correlation matrix",
    "tool_name": "visualize:correlation",
    "tool_args": {
        "data": [
            {"a": 1, "b": 2, "c": 3},
            {"a": 2, "b": 4, "c": 5}
        ],
        "columns": ["a", "b", "c"],
        "title": "Variable Correlations",
        "filename": "correlations"
    }
}
~~~

11. 3D scatter plot
~~~json
{
    "thoughts": [
        "Need to visualize 3D relationships..."
    ],
    "headline": "Creating 3D scatter visualization",
    "tool_name": "visualize:scatter_3d",
    "tool_args": {
        "data": [
            {"x": 1, "y": 2, "z": 3, "label": "A"},
            {"x": 2, "y": 3, "z": 4, "label": "B"}
        ],
        "x": "x",
        "y": "y",
        "z": "z",
        "color": "label",
        "title": "3D Data Visualization",
        "filename": "scatter3d"
    }
}
~~~
