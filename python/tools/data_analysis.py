"""
Data Analysis Tool

This tool provides advanced data analysis capabilities using DuckDB
for high-performance queries, vector similarity search, and statistical analysis.
"""

import json
import os
from typing import Any, Dict, List, Optional

from python.helpers.tool import Tool, Response
from python.helpers.duckdb_analysis import DuckDBAnalysis, get_duckdb_analysis
from python.helpers.print_style import PrintStyle


class DataAnalysis(Tool):
    """
    Data analysis tool for executing analytical queries and data operations.
    
    Methods:
        query: Execute a SQL query
        import_data: Import data from files (CSV, JSON, Parquet)
        export_data: Export data to files
        statistics: Get descriptive statistics
        aggregate: Perform aggregation queries
        vector_search: Search for similar vectors
        spatial_query: Perform spatial queries
    """
    
    async def execute(self, **kwargs) -> Response:
        """Execute the data analysis tool based on method."""
        method = self.method or kwargs.get("method", "query")
        
        # Get or create DuckDB instance
        db_path = kwargs.get("database", ":memory:")
        self._db = get_duckdb_analysis(db_path)
        
        try:
            if method == "query":
                return await self._execute_query(**kwargs)
            elif method == "import_data":
                return await self._import_data(**kwargs)
            elif method == "export_data":
                return await self._export_data(**kwargs)
            elif method == "statistics":
                return await self._get_statistics(**kwargs)
            elif method == "aggregate":
                return await self._aggregate(**kwargs)
            elif method == "vector_search":
                return await self._vector_search(**kwargs)
            elif method == "spatial_query":
                return await self._spatial_query(**kwargs)
            elif method == "create_table":
                return await self._create_table(**kwargs)
            elif method == "list_tables":
                return await self._list_tables(**kwargs)
            else:
                return Response(
                    message=f"Unknown method: {method}. Available methods: query, import_data, export_data, statistics, aggregate, vector_search, spatial_query, create_table, list_tables",
                    break_loop=False
                )
        except Exception as e:
            return Response(
                message=f"Data analysis error: {str(e)}",
                break_loop=False
            )
    
    async def _execute_query(self, **kwargs) -> Response:
        """Execute a SQL query."""
        query = kwargs.get("query", "")
        params = kwargs.get("parameters", None)
        
        if not query:
            return Response(message="No query provided", break_loop=False)
        
        result = self._db.execute(query, params)
        
        # Format response
        response_parts = []
        response_parts.append(f"Query executed in {result.get('execution_time_ms', 0):.2f}ms")
        response_parts.append(f"Rows returned: {result.get('row_count', 0)}")
        
        if result.get("columns"):
            response_parts.append(f"Columns: {', '.join(result['columns'])}")
        
        if result.get("data"):
            # Truncate if too many rows
            data = result["data"]
            if len(data) > 100:
                response_parts.append(f"\nShowing first 100 of {len(data)} rows:")
                data = data[:100]
            else:
                response_parts.append("\nResults:")
            
            response_parts.append(json.dumps(data, indent=2, default=str))
        
        return Response(message="\n".join(response_parts), break_loop=False)
    
    async def _import_data(self, **kwargs) -> Response:
        """Import data from a file."""
        file_path = kwargs.get("file_path", "")
        table_name = kwargs.get("table_name", "")
        file_format = kwargs.get("format", "").lower()
        
        if not file_path:
            return Response(message="No file path provided", break_loop=False)
        if not table_name:
            return Response(message="No table name provided", break_loop=False)
        
        # Auto-detect format from extension if not provided
        if not file_format:
            ext = os.path.splitext(file_path)[1].lower()
            format_map = {".csv": "csv", ".json": "json", ".parquet": "parquet"}
            file_format = format_map.get(ext, "csv")
        
        success = False
        if file_format == "csv":
            delimiter = kwargs.get("delimiter", ",")
            header = kwargs.get("header", True)
            success = self._db.import_csv(file_path, table_name, delimiter=delimiter, header=header)
        elif file_format == "json":
            success = self._db.import_json(file_path, table_name)
        elif file_format == "parquet":
            success = self._db.import_parquet(file_path, table_name)
        else:
            return Response(message=f"Unsupported format: {file_format}", break_loop=False)
        
        if success:
            return Response(
                message=f"Successfully imported {file_path} to table '{table_name}'",
                break_loop=False
            )
        else:
            return Response(
                message=f"Failed to import {file_path}",
                break_loop=False
            )
    
    async def _export_data(self, **kwargs) -> Response:
        """Export data to a file."""
        source = kwargs.get("source", "")  # Table name or query
        file_path = kwargs.get("file_path", "")
        file_format = kwargs.get("format", "csv").lower()
        
        if not source:
            return Response(message="No source (table or query) provided", break_loop=False)
        if not file_path:
            return Response(message="No file path provided", break_loop=False)
        
        success = False
        if file_format == "csv":
            success = self._db.export_csv(source, file_path)
        elif file_format == "json":
            success = self._db.export_json(source, file_path)
        elif file_format == "parquet":
            success = self._db.export_parquet(source, file_path)
        else:
            return Response(message=f"Unsupported format: {file_format}", break_loop=False)
        
        if success:
            return Response(
                message=f"Successfully exported to {file_path}",
                break_loop=False
            )
        else:
            return Response(
                message=f"Failed to export to {file_path}",
                break_loop=False
            )
    
    async def _get_statistics(self, **kwargs) -> Response:
        """Get descriptive statistics for a table."""
        table_name = kwargs.get("table_name", "")
        columns = kwargs.get("columns", None)
        
        if not table_name:
            return Response(message="No table name provided", break_loop=False)
        
        stats = self._db.describe_statistics(table_name, columns)
        
        if stats:
            return Response(
                message=f"Statistics for {table_name}:\n{json.dumps(stats, indent=2, default=str)}",
                break_loop=False
            )
        else:
            return Response(
                message=f"No statistics available for {table_name}",
                break_loop=False
            )
    
    async def _aggregate(self, **kwargs) -> Response:
        """Perform aggregation query."""
        table_name = kwargs.get("table_name", "")
        group_by = kwargs.get("group_by", [])
        aggregations = kwargs.get("aggregations", {})
        where = kwargs.get("where", None)
        having = kwargs.get("having", None)
        order_by = kwargs.get("order_by", None)
        limit = kwargs.get("limit", None)
        
        if not table_name:
            return Response(message="No table name provided", break_loop=False)
        if not aggregations:
            return Response(message="No aggregations specified", break_loop=False)
        
        result = self._db.aggregate(
            table_name=table_name,
            group_by=group_by if isinstance(group_by, list) else [group_by],
            aggregations=aggregations,
            where=where,
            having=having,
            order_by=order_by,
            limit=limit
        )
        
        return Response(
            message=f"Aggregation results:\n{json.dumps(result.get('data', []), indent=2, default=str)}",
            break_loop=False
        )
    
    async def _vector_search(self, **kwargs) -> Response:
        """Search for similar vectors."""
        table_name = kwargs.get("table_name", "")
        query_vector = kwargs.get("query_vector", [])
        limit = kwargs.get("limit", 10)
        metric = kwargs.get("metric", "cosine")
        filter_condition = kwargs.get("filter", None)
        
        if not table_name:
            return Response(message="No table name provided", break_loop=False)
        if not query_vector:
            return Response(message="No query vector provided", break_loop=False)
        
        results = self._db.search_vectors(
            table_name=table_name,
            query_vector=query_vector,
            limit=limit,
            metric=metric,
            filter_condition=filter_condition
        )
        
        return Response(
            message=f"Vector search results ({len(results)} matches):\n{json.dumps(results, indent=2, default=str)}",
            break_loop=False
        )
    
    async def _spatial_query(self, **kwargs) -> Response:
        """Perform a spatial query."""
        table_name = kwargs.get("table_name", "")
        query_geom = kwargs.get("geometry", "")
        operation = kwargs.get("operation", "intersects")
        distance = kwargs.get("distance", None)
        limit = kwargs.get("limit", 100)
        
        if not table_name:
            return Response(message="No table name provided", break_loop=False)
        if not query_geom:
            return Response(message="No query geometry provided", break_loop=False)
        
        results = self._db.spatial_query(
            table_name=table_name,
            query_geom=query_geom,
            operation=operation,
            distance=distance,
            limit=limit
        )
        
        return Response(
            message=f"Spatial query results ({len(results)} features):\n{json.dumps(results, indent=2, default=str)}",
            break_loop=False
        )
    
    async def _create_table(self, **kwargs) -> Response:
        """Create a new table."""
        table_name = kwargs.get("table_name", "")
        schema = kwargs.get("schema", {})
        table_type = kwargs.get("type", "standard")  # standard, vector, spatial
        
        if not table_name:
            return Response(message="No table name provided", break_loop=False)
        
        success = False
        if table_type == "vector":
            dimensions = kwargs.get("dimensions", 384)
            additional_cols = kwargs.get("additional_columns", None)
            success = self._db.create_vector_table(table_name, dimensions, additional_cols)
        elif table_type == "spatial":
            geometry_type = kwargs.get("geometry_type", "GEOMETRY")
            srid = kwargs.get("srid", 4326)
            additional_cols = kwargs.get("additional_columns", None)
            success = self._db.create_spatial_table(table_name, geometry_type, srid, additional_cols)
        else:
            if not schema:
                return Response(message="No schema provided for standard table", break_loop=False)
            success = self._db.create_table(table_name, schema)
        
        if success:
            return Response(
                message=f"Successfully created {table_type} table '{table_name}'",
                break_loop=False
            )
        else:
            return Response(
                message=f"Failed to create table '{table_name}'",
                break_loop=False
            )
    
    async def _list_tables(self, **kwargs) -> Response:
        """List all tables in the database."""
        tables = self._db.list_tables()
        
        if tables:
            return Response(
                message=f"Tables in database:\n" + "\n".join(f"  - {t}" for t in tables),
                break_loop=False
            )
        else:
            return Response(
                message="No tables found in database",
                break_loop=False
            )
