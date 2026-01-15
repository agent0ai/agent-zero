### data_analysis
high-performance analytical database for data analysis
uses DuckDB with vector similarity, spatial, and JSON support
methods: query, import_data, export_data, statistics, aggregate, vector_search, spatial_query, create_table, list_tables
default database is in-memory, specify "database" arg for persistent storage

1. execute SQL query
~~~json
{
    "thoughts": [
        "Need to analyze data...",
        "Let me query the table..."
    ],
    "headline": "Executing SQL query for data analysis",
    "tool_name": "data_analysis:query",
    "tool_args": {
        "query": "SELECT category, SUM(amount) as total FROM sales GROUP BY category ORDER BY total DESC",
        "database": ":memory:"
    }
}
~~~

2. import data from file
~~~json
{
    "thoughts": [
        "Need to load data from CSV file..."
    ],
    "headline": "Importing CSV data into analysis database",
    "tool_name": "data_analysis:import_data",
    "tool_args": {
        "file_path": "/path/to/data.csv",
        "table_name": "my_data",
        "format": "csv",
        "delimiter": ",",
        "header": true
    }
}
~~~

3. get descriptive statistics
~~~json
{
    "thoughts": [
        "Need to understand data distribution..."
    ],
    "headline": "Getting statistics for numeric columns",
    "tool_name": "data_analysis:statistics",
    "tool_args": {
        "table_name": "my_data",
        "columns": ["price", "quantity"]
    }
}
~~~

4. aggregation query
~~~json
{
    "thoughts": [
        "Need to aggregate data by groups..."
    ],
    "headline": "Performing aggregation analysis",
    "tool_name": "data_analysis:aggregate",
    "tool_args": {
        "table_name": "sales",
        "group_by": ["region", "product"],
        "aggregations": {
            "total_sales": "SUM(amount)",
            "avg_price": "AVG(price)",
            "count": "COUNT(*)"
        },
        "where": "year = 2024",
        "order_by": "total_sales DESC",
        "limit": 20
    }
}
~~~

5. vector similarity search
~~~json
{
    "thoughts": [
        "Need to find similar items by embedding..."
    ],
    "headline": "Searching for similar vectors",
    "tool_name": "data_analysis:vector_search",
    "tool_args": {
        "table_name": "embeddings",
        "query_vector": [0.1, 0.2, 0.3, ...],
        "limit": 10,
        "metric": "cosine"
    }
}
~~~

6. create vector table
~~~json
{
    "thoughts": [
        "Need to store embeddings..."
    ],
    "headline": "Creating vector storage table",
    "tool_name": "data_analysis:create_table",
    "tool_args": {
        "table_name": "embeddings",
        "type": "vector",
        "dimensions": 384
    }
}
~~~

7. export data
~~~json
{
    "thoughts": [
        "Need to export results..."
    ],
    "headline": "Exporting query results to file",
    "tool_name": "data_analysis:export_data",
    "tool_args": {
        "source": "SELECT * FROM analysis_results",
        "file_path": "/path/to/output.parquet",
        "format": "parquet"
    }
}
~~~

8. spatial query
~~~json
{
    "thoughts": [
        "Need to find locations within area..."
    ],
    "headline": "Performing spatial query",
    "tool_name": "data_analysis:spatial_query",
    "tool_args": {
        "table_name": "locations",
        "geometry": "POINT(-122.4194 37.7749)",
        "operation": "distance",
        "distance": 0.1,
        "limit": 50
    }
}
~~~
