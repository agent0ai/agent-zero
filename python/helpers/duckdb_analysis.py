"""
DuckDB Analysis Helper

This module provides a high-performance analytical database system using DuckDB,
designed for complex data analysis, vector similarity search, spatial queries,
and JSON schema validation within Agent Zero.

Features:
- High-performance OLAP queries
- Vector Similarity Search (VSS) for embeddings
- Spatial data support for geographic analysis
- JSON schema validation
- In-memory and persistent storage modes
- Integration with existing Agent Zero patterns
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple, TypedDict, Union
from dataclasses import dataclass, field
import tempfile

from python.helpers.print_style import PrintStyle
from python.helpers import files


@dataclass
class DuckDBConfig:
    """Configuration for DuckDB connection."""
    database_path: str = ":memory:"  # Use :memory: for in-memory database
    extensions: List[str] = field(default_factory=lambda: [
        "vss",        # Vector similarity search
        "spatial",    # Spatial/geographic operations
        "json",       # JSON operations (built-in but good to specify)
    ])
    read_only: bool = False
    threads: int = 0  # 0 = auto-detect
    
    @classmethod
    def from_env(cls) -> "DuckDBConfig":
        """Create config from environment variables."""
        extensions_str = os.getenv("DUCKDB_EXTENSIONS", "vss,spatial,json")
        extensions = [ext.strip() for ext in extensions_str.split(",") if ext.strip()]
        
        return cls(
            database_path=os.getenv("DUCKDB_PATH", ":memory:"),
            extensions=extensions,
            read_only=os.getenv("DUCKDB_READONLY", "false").lower() == "true",
            threads=int(os.getenv("DUCKDB_THREADS", "0")),
        )


class AnalysisResult(TypedDict, total=False):
    """Result from an analysis query."""
    data: List[Dict[str, Any]]
    columns: List[str]
    row_count: int
    execution_time_ms: float
    query: str


class DuckDBAnalysis:
    """
    DuckDB-based analytical database for high-performance data analysis.
    
    This class provides methods for complex queries, vector similarity search,
    spatial analysis, and structured data operations.
    """
    
    # Singleton instances by database path
    _instances: Dict[str, "DuckDBAnalysis"] = {}
    
    def __init__(self, config: Optional[DuckDBConfig] = None):
        """Initialize DuckDB analysis engine."""
        self.config = config or DuckDBConfig.from_env()
        self._conn = None
        self._connected = False
        self._extensions_loaded: List[str] = []
        
    @classmethod
    def get_instance(
        cls,
        database_path: str = ":memory:",
        config: Optional[DuckDBConfig] = None
    ) -> "DuckDBAnalysis":
        """Get or create a singleton instance for the specified database."""
        if database_path not in cls._instances:
            if config:
                cfg = config
            else:
                cfg = DuckDBConfig.from_env()
                cfg.database_path = database_path
            cls._instances[database_path] = cls(cfg)
        return cls._instances[database_path]
    
    def connect(self) -> bool:
        """Establish connection to DuckDB."""
        if self._connected and self._conn:
            return True
            
        try:
            import duckdb
            
            # Connect with configuration
            self._conn = duckdb.connect(
                database=self.config.database_path,
                read_only=self.config.read_only,
            )
            
            # Set thread count if specified
            if self.config.threads > 0:
                self._conn.execute(f"SET threads={self.config.threads}")
            
            self._connected = True
            
            # Load extensions
            self._load_extensions()
            
            PrintStyle.standard(
                f"Connected to DuckDB: {self.config.database_path}"
            )
            return True
        except ImportError:
            PrintStyle.warning(
                "DuckDB package not installed. Install with: pip install duckdb"
            )
            return False
        except Exception as e:
            PrintStyle.error(f"Failed to connect to DuckDB: {e}")
            self._connected = False
            return False
    
    def _load_extensions(self) -> None:
        """Load configured DuckDB extensions."""
        if not self._conn:
            return
            
        for ext in self.config.extensions:
            try:
                # Install if not already installed
                self._conn.execute(f"INSTALL {ext};")
                self._conn.execute(f"LOAD {ext};")
                self._extensions_loaded.append(ext)
                PrintStyle.standard(f"Loaded DuckDB extension: {ext}")
            except Exception as e:
                # Some extensions might already be loaded or not available
                PrintStyle.warning(f"Could not load extension {ext}: {e}")
    
    def disconnect(self) -> None:
        """Close connection to DuckDB."""
        if self._conn and self._connected:
            try:
                self._conn.close()
            except Exception:
                pass
            finally:
                self._connected = False
                self._conn = None
    
    def execute(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> AnalysisResult:
        """
        Execute a SQL query and return results.
        
        Args:
            query: SQL query string
            parameters: Query parameters for prepared statements
            
        Returns:
            AnalysisResult with data, columns, and metadata
        """
        if not self.connect():
            return AnalysisResult(data=[], columns=[], row_count=0, query=query)
            
        try:
            import time
            start_time = time.time()
            
            if parameters:
                # Use named parameters
                result = self._conn.execute(query, parameters)
            else:
                result = self._conn.execute(query)
            
            # Fetch results
            columns = [desc[0] for desc in result.description] if result.description else []
            rows = result.fetchall()
            data = [dict(zip(columns, row)) for row in rows]
            
            execution_time = (time.time() - start_time) * 1000
            
            return AnalysisResult(
                data=data,
                columns=columns,
                row_count=len(data),
                execution_time_ms=execution_time,
                query=query,
            )
        except Exception as e:
            PrintStyle.error(f"Query execution failed: {e}")
            return AnalysisResult(
                data=[],
                columns=[],
                row_count=0,
                query=query,
            )
    
    def execute_many(
        self,
        query: str,
        data: List[Tuple],
    ) -> bool:
        """Execute a query with multiple parameter sets."""
        if not self.connect():
            return False
            
        try:
            self._conn.executemany(query, data)
            return True
        except Exception as e:
            PrintStyle.error(f"Batch execution failed: {e}")
            return False
    
    # ========== Table Operations ==========
    
    def create_table(
        self,
        table_name: str,
        schema: Dict[str, str],
        if_not_exists: bool = True,
    ) -> bool:
        """
        Create a table with the specified schema.
        
        Args:
            table_name: Name of the table
            schema: Column definitions (name -> type)
            if_not_exists: Don't error if table exists
            
        Returns:
            True if successful
        """
        if not self.connect():
            return False
            
        try:
            columns = ", ".join([f"{col} {dtype}" for col, dtype in schema.items()])
            exists_clause = "IF NOT EXISTS " if if_not_exists else ""
            query = f"CREATE TABLE {exists_clause}{table_name} ({columns})"
            self._conn.execute(query)
            return True
        except Exception as e:
            PrintStyle.error(f"Failed to create table: {e}")
            return False
    
    def drop_table(self, table_name: str, if_exists: bool = True) -> bool:
        """Drop a table."""
        if not self.connect():
            return False
            
        try:
            exists_clause = "IF EXISTS " if if_exists else ""
            self._conn.execute(f"DROP TABLE {exists_clause}{table_name}")
            return True
        except Exception as e:
            PrintStyle.error(f"Failed to drop table: {e}")
            return False
    
    def list_tables(self) -> List[str]:
        """List all tables in the database."""
        result = self.execute("SHOW TABLES")
        return [row.get("name", "") for row in result["data"]]
    
    def describe_table(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information."""
        result = self.execute(f"DESCRIBE {table_name}")
        return result["data"]
    
    # ========== Data Import/Export ==========
    
    def import_csv(
        self,
        file_path: str,
        table_name: str,
        auto_detect: bool = True,
        delimiter: str = ",",
        header: bool = True,
    ) -> bool:
        """Import data from a CSV file."""
        if not self.connect():
            return False
            
        try:
            options = []
            if auto_detect:
                options.append("AUTO_DETECT=TRUE")
            options.append(f"DELIM='{delimiter}'")
            options.append(f"HEADER={'TRUE' if header else 'FALSE'}")
            
            options_str = ", ".join(options)
            query = f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM read_csv_auto('{file_path}', {options_str})"
            self._conn.execute(query)
            return True
        except Exception as e:
            PrintStyle.error(f"Failed to import CSV: {e}")
            return False
    
    def import_json(
        self,
        file_path: str,
        table_name: str,
        auto_detect: bool = True,
    ) -> bool:
        """Import data from a JSON file."""
        if not self.connect():
            return False
            
        try:
            options = "AUTO_DETECT=TRUE" if auto_detect else ""
            query = f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM read_json_auto('{file_path}')"
            self._conn.execute(query)
            return True
        except Exception as e:
            PrintStyle.error(f"Failed to import JSON: {e}")
            return False
    
    def import_parquet(self, file_path: str, table_name: str) -> bool:
        """Import data from a Parquet file."""
        if not self.connect():
            return False
            
        try:
            query = f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM parquet_scan('{file_path}')"
            self._conn.execute(query)
            return True
        except Exception as e:
            PrintStyle.error(f"Failed to import Parquet: {e}")
            return False
    
    def export_csv(self, query_or_table: str, file_path: str) -> bool:
        """Export query results or table to CSV."""
        if not self.connect():
            return False
            
        try:
            # Check if it's a table name or query
            if " " not in query_or_table:
                source = f"SELECT * FROM {query_or_table}"
            else:
                source = query_or_table
                
            export_query = f"COPY ({source}) TO '{file_path}' (FORMAT CSV, HEADER TRUE)"
            self._conn.execute(export_query)
            return True
        except Exception as e:
            PrintStyle.error(f"Failed to export CSV: {e}")
            return False
    
    def export_json(self, query_or_table: str, file_path: str) -> bool:
        """Export query results or table to JSON."""
        if not self.connect():
            return False
            
        try:
            if " " not in query_or_table:
                source = f"SELECT * FROM {query_or_table}"
            else:
                source = query_or_table
                
            export_query = f"COPY ({source}) TO '{file_path}' (FORMAT JSON)"
            self._conn.execute(export_query)
            return True
        except Exception as e:
            PrintStyle.error(f"Failed to export JSON: {e}")
            return False
    
    def export_parquet(self, query_or_table: str, file_path: str) -> bool:
        """Export query results or table to Parquet."""
        if not self.connect():
            return False
            
        try:
            if " " not in query_or_table:
                source = f"SELECT * FROM {query_or_table}"
            else:
                source = query_or_table
                
            export_query = f"COPY ({source}) TO '{file_path}' (FORMAT PARQUET)"
            self._conn.execute(export_query)
            return True
        except Exception as e:
            PrintStyle.error(f"Failed to export Parquet: {e}")
            return False
    
    # ========== Vector Similarity Search (VSS) ==========
    
    def create_vector_table(
        self,
        table_name: str,
        dimensions: int,
        additional_columns: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Create a table optimized for vector similarity search.
        
        Args:
            table_name: Name of the table
            dimensions: Dimension of the embedding vectors
            additional_columns: Extra columns beyond id and embedding
        """
        if not self.connect():
            return False
            
        if "vss" not in self._extensions_loaded:
            PrintStyle.warning("VSS extension not loaded. Vector operations may be limited.")
            
        try:
            # Build schema
            schema = {
                "id": "VARCHAR PRIMARY KEY",
                "embedding": f"FLOAT[{dimensions}]",
                "content": "TEXT",
                "metadata": "JSON",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            }
            
            if additional_columns:
                schema.update(additional_columns)
                
            return self.create_table(table_name, schema)
        except Exception as e:
            PrintStyle.error(f"Failed to create vector table: {e}")
            return False
    
    def insert_vectors(
        self,
        table_name: str,
        vectors: List[Dict[str, Any]],
    ) -> int:
        """
        Insert vectors into the table.
        
        Args:
            table_name: Target table
            vectors: List of dicts with 'id', 'embedding', 'content', 'metadata'
            
        Returns:
            Number of inserted rows
        """
        if not self.connect() or not vectors:
            return 0
            
        try:
            inserted = 0
            for vec in vectors:
                vec_id = vec.get("id")
                embedding = vec.get("embedding", [])
                content = vec.get("content", "")
                metadata = json.dumps(vec.get("metadata", {}))
                
                # Convert embedding to array format
                embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
                
                query = f"""
                    INSERT INTO {table_name} (id, embedding, content, metadata)
                    VALUES (?, {embedding_str}::FLOAT[{len(embedding)}], ?, ?::JSON)
                """
                self._conn.execute(query, [vec_id, content, metadata])
                inserted += 1
                
            return inserted
        except Exception as e:
            PrintStyle.error(f"Failed to insert vectors: {e}")
            return 0
    
    def search_vectors(
        self,
        table_name: str,
        query_vector: List[float],
        limit: int = 10,
        metric: str = "cosine",  # cosine, l2, inner_product
        filter_condition: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            table_name: Table to search
            query_vector: Query embedding
            limit: Maximum results
            metric: Distance metric (cosine, l2, inner_product)
            filter_condition: Optional WHERE clause
            
        Returns:
            List of similar items with distances
        """
        if not self.connect():
            return []
            
        try:
            # Build distance expression based on metric
            vec_str = "[" + ",".join(str(x) for x in query_vector) + "]"
            
            if metric == "cosine":
                # Cosine similarity (higher is better, so we sort descending)
                distance_expr = f"list_cosine_similarity(embedding, {vec_str}::FLOAT[{len(query_vector)}])"
                order = "DESC"
            elif metric == "inner_product":
                distance_expr = f"list_inner_product(embedding, {vec_str}::FLOAT[{len(query_vector)}])"
                order = "DESC"
            else:  # l2/euclidean
                distance_expr = f"list_distance(embedding, {vec_str}::FLOAT[{len(query_vector)}])"
                order = "ASC"
            
            where_clause = f"WHERE {filter_condition}" if filter_condition else ""
            
            query = f"""
                SELECT id, content, metadata, {distance_expr} as similarity
                FROM {table_name}
                {where_clause}
                ORDER BY similarity {order}
                LIMIT {limit}
            """
            
            result = self.execute(query)
            return result["data"]
        except Exception as e:
            PrintStyle.error(f"Vector search failed: {e}")
            return []
    
    # ========== Spatial Operations ==========
    
    def create_spatial_table(
        self,
        table_name: str,
        geometry_type: str = "GEOMETRY",
        srid: int = 4326,
        additional_columns: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Create a table with spatial/geometry support.
        
        Args:
            table_name: Name of the table
            geometry_type: Type of geometry (POINT, LINESTRING, POLYGON, etc.)
            srid: Spatial Reference ID (4326 = WGS84)
            additional_columns: Extra columns
        """
        if not self.connect():
            return False
            
        if "spatial" not in self._extensions_loaded:
            PrintStyle.warning("Spatial extension not loaded. Spatial operations may be limited.")
            
        try:
            schema = {
                "id": "VARCHAR PRIMARY KEY",
                "geom": geometry_type,
                "properties": "JSON",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            }
            
            if additional_columns:
                schema.update(additional_columns)
                
            return self.create_table(table_name, schema)
        except Exception as e:
            PrintStyle.error(f"Failed to create spatial table: {e}")
            return False
    
    def insert_geometry(
        self,
        table_name: str,
        geom_id: str,
        wkt_or_geojson: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Insert a geometry into a spatial table.
        
        Args:
            table_name: Target table
            geom_id: Unique identifier
            wkt_or_geojson: Geometry in WKT or GeoJSON format
            properties: Additional properties as JSON
        """
        if not self.connect():
            return False
            
        try:
            props_json = json.dumps(properties or {})
            
            # Detect format and convert
            if wkt_or_geojson.strip().startswith("{"):
                # GeoJSON
                geom_expr = f"ST_GeomFromGeoJSON('{wkt_or_geojson}')"
            else:
                # WKT
                geom_expr = f"ST_GeomFromText('{wkt_or_geojson}')"
            
            query = f"""
                INSERT INTO {table_name} (id, geom, properties)
                VALUES (?, {geom_expr}, ?::JSON)
            """
            self._conn.execute(query, [geom_id, props_json])
            return True
        except Exception as e:
            PrintStyle.error(f"Failed to insert geometry: {e}")
            return False
    
    def spatial_query(
        self,
        table_name: str,
        query_geom: str,
        operation: str = "intersects",  # intersects, contains, within, distance
        distance: Optional[float] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Perform a spatial query.
        
        Args:
            table_name: Table to query
            query_geom: Query geometry (WKT or GeoJSON)
            operation: Spatial operation
            distance: Distance threshold for distance queries (in degrees for WGS84)
            limit: Maximum results
        """
        if not self.connect():
            return []
            
        try:
            # Parse query geometry
            if query_geom.strip().startswith("{"):
                geom_expr = f"ST_GeomFromGeoJSON('{query_geom}')"
            else:
                geom_expr = f"ST_GeomFromText('{query_geom}')"
            
            # Build spatial predicate
            if operation == "intersects":
                predicate = f"ST_Intersects(geom, {geom_expr})"
            elif operation == "contains":
                predicate = f"ST_Contains(geom, {geom_expr})"
            elif operation == "within":
                predicate = f"ST_Within(geom, {geom_expr})"
            elif operation == "distance" and distance is not None:
                predicate = f"ST_DWithin(geom, {geom_expr}, {distance})"
            else:
                predicate = f"ST_Intersects(geom, {geom_expr})"
            
            query = f"""
                SELECT id, ST_AsGeoJSON(geom) as geometry, properties
                FROM {table_name}
                WHERE {predicate}
                LIMIT {limit}
            """
            
            result = self.execute(query)
            
            # Parse GeoJSON strings back to objects
            for row in result["data"]:
                if "geometry" in row and isinstance(row["geometry"], str):
                    try:
                        row["geometry"] = json.loads(row["geometry"])
                    except:
                        pass
                        
            return result["data"]
        except Exception as e:
            PrintStyle.error(f"Spatial query failed: {e}")
            return []
    
    # ========== JSON Operations ==========
    
    def validate_json_schema(
        self,
        data: Union[str, Dict],
        schema: Dict[str, Any],
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate JSON data against a schema.
        
        Note: This is a Python-level validation, not DuckDB native.
        For production use, consider using jsonschema library.
        
        Args:
            data: JSON data to validate
            schema: JSON Schema definition
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            from jsonschema import validate, ValidationError
            
            if isinstance(data, str):
                data = json.loads(data)
                
            validate(instance=data, schema=schema)
            return True, None
        except ImportError:
            PrintStyle.warning("jsonschema not installed. Install with: pip install jsonschema")
            return True, "Schema validation skipped (jsonschema not installed)"
        except Exception as e:
            return False, str(e)
    
    def json_extract(
        self,
        table_name: str,
        json_column: str,
        json_path: str,
        alias: str = "extracted",
    ) -> AnalysisResult:
        """
        Extract values from a JSON column.
        
        Args:
            table_name: Source table
            json_column: Column containing JSON
            json_path: JSONPath expression
            alias: Column alias for extracted value
        """
        query = f"""
            SELECT *, json_extract({json_column}, '{json_path}') as {alias}
            FROM {table_name}
        """
        return self.execute(query)
    
    # ========== Analytics Functions ==========
    
    def aggregate(
        self,
        table_name: str,
        group_by: List[str],
        aggregations: Dict[str, str],
        where: Optional[str] = None,
        having: Optional[str] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> AnalysisResult:
        """
        Perform aggregation queries.
        
        Args:
            table_name: Source table
            group_by: Columns to group by
            aggregations: Dict of alias -> aggregation expression
            where: WHERE clause
            having: HAVING clause
            order_by: ORDER BY clause
            limit: LIMIT value
        """
        # Build SELECT clause
        select_parts = list(group_by) + [f"{expr} as {alias}" for alias, expr in aggregations.items()]
        select_clause = ", ".join(select_parts)
        
        # Build GROUP BY
        group_clause = ", ".join(group_by) if group_by else ""
        
        # Build query
        query = f"SELECT {select_clause} FROM {table_name}"
        
        if where:
            query += f" WHERE {where}"
        if group_clause:
            query += f" GROUP BY {group_clause}"
        if having:
            query += f" HAVING {having}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit:
            query += f" LIMIT {limit}"
            
        return self.execute(query)
    
    def window_function(
        self,
        table_name: str,
        select_cols: List[str],
        window_expr: str,
        alias: str,
        partition_by: Optional[str] = None,
        order_by: Optional[str] = None,
        where: Optional[str] = None,
    ) -> AnalysisResult:
        """
        Execute a window function query.
        
        Args:
            table_name: Source table
            select_cols: Base columns to select
            window_expr: Window function expression (e.g., "ROW_NUMBER()")
            alias: Alias for the window result
            partition_by: PARTITION BY clause
            order_by: ORDER BY within window
            where: WHERE clause
        """
        window_clause = f"OVER ("
        if partition_by:
            window_clause += f"PARTITION BY {partition_by} "
        if order_by:
            window_clause += f"ORDER BY {order_by}"
        window_clause += ")"
        
        select_list = ", ".join(select_cols + [f"{window_expr} {window_clause} as {alias}"])
        
        query = f"SELECT {select_list} FROM {table_name}"
        if where:
            query += f" WHERE {where}"
            
        return self.execute(query)
    
    def pivot(
        self,
        table_name: str,
        value_col: str,
        pivot_col: str,
        agg_func: str = "SUM",
        group_cols: Optional[List[str]] = None,
    ) -> AnalysisResult:
        """
        Create a pivot table.
        
        Args:
            table_name: Source table
            value_col: Column to aggregate
            pivot_col: Column to pivot on
            agg_func: Aggregation function
            group_cols: Additional grouping columns
        """
        query = f"""
            PIVOT {table_name}
            ON {pivot_col}
            USING {agg_func}({value_col})
        """
        
        if group_cols:
            query += f" GROUP BY {', '.join(group_cols)}"
            
        return self.execute(query)
    
    def time_series_analysis(
        self,
        table_name: str,
        time_col: str,
        value_col: str,
        interval: str = "day",
        agg_func: str = "AVG",
        where: Optional[str] = None,
    ) -> AnalysisResult:
        """
        Perform time series aggregation.
        
        Args:
            table_name: Source table
            time_col: Timestamp column
            value_col: Value column to aggregate
            interval: Time bucket (second, minute, hour, day, week, month, year)
            agg_func: Aggregation function
            where: WHERE clause
        """
        query = f"""
            SELECT 
                date_trunc('{interval}', {time_col}) as time_bucket,
                {agg_func}({value_col}) as value,
                COUNT(*) as count
            FROM {table_name}
        """
        
        if where:
            query += f" WHERE {where}"
            
        query += f" GROUP BY time_bucket ORDER BY time_bucket"
        
        return self.execute(query)
    
    def describe_statistics(self, table_name: str, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get descriptive statistics for numeric columns.
        
        Args:
            table_name: Table to analyze
            columns: Specific columns (None = all numeric)
        """
        if not self.connect():
            return {}
            
        try:
            # Get table schema
            schema = self.describe_table(table_name)
            numeric_types = ["INTEGER", "BIGINT", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC"]
            
            if columns:
                target_cols = columns
            else:
                target_cols = [
                    col["column_name"] for col in schema
                    if any(t in col.get("column_type", "").upper() for t in numeric_types)
                ]
            
            if not target_cols:
                return {}
                
            stats = {}
            for col in target_cols:
                result = self.execute(f"""
                    SELECT 
                        COUNT(*) as count,
                        AVG({col}) as mean,
                        STDDEV({col}) as std,
                        MIN({col}) as min,
                        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY {col}) as q25,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {col}) as median,
                        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY {col}) as q75,
                        MAX({col}) as max
                    FROM {table_name}
                """)
                if result["data"]:
                    stats[col] = result["data"][0]
                    
            return stats
        except Exception as e:
            PrintStyle.error(f"Failed to compute statistics: {e}")
            return {}


# Helper function for agent integration
def get_duckdb_analysis(
    database_path: str = ":memory:",
    extensions: Optional[List[str]] = None,
) -> DuckDBAnalysis:
    """
    Get a configured DuckDB analysis instance.
    
    Args:
        database_path: Path to database file or :memory:
        extensions: List of extensions to load
        
    Returns:
        Configured DuckDBAnalysis instance
    """
    config = DuckDBConfig.from_env()
    config.database_path = database_path
    if extensions:
        config.extensions = extensions
        
    instance = DuckDBAnalysis.get_instance(database_path, config)
    instance.connect()
    return instance
