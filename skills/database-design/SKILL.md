---
name: "database-design"
description: "Database design, schema optimization, and query best practices. Use when designing schemas, optimizing queries, or working with databases."
version: "1.0.0"
author: "Agent Zero Team"
tags: ["database", "sql", "schema", "optimization", "postgresql", "mysql"]
trigger_patterns:
  - "database"
  - "schema"
  - "sql"
  - "query"
  - "table"
  - "index"
---

# Database Design Skill

Best practices for schema design, query optimization, and database management.

## Schema Design Principles

### Normalization

**1NF (First Normal Form)**
- Each column contains atomic values
- No repeating groups

**2NF (Second Normal Form)**
- Meet 1NF
- No partial dependencies (all non-key columns depend on the entire primary key)

**3NF (Third Normal Form)**
- Meet 2NF
- No transitive dependencies (non-key columns don't depend on other non-key columns)

### Example: Normalized Schema

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Addresses table (1:N relationship)
CREATE TABLE addresses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    street VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    postal_code VARCHAR(20),
    is_primary BOOLEAN DEFAULT FALSE
);

-- Orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    address_id INTEGER REFERENCES addresses(id),
    status VARCHAR(50) DEFAULT 'pending',
    total_amount DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items (N:N through junction table)
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL
);
```

### When to Denormalize

Consider denormalization for:
- Read-heavy workloads
- Frequently joined tables
- Reporting/analytics queries

```sql
-- Denormalized order summary (materialized view)
CREATE MATERIALIZED VIEW order_summaries AS
SELECT
    o.id,
    o.created_at,
    u.name AS user_name,
    u.email AS user_email,
    a.city AS shipping_city,
    o.total_amount,
    COUNT(oi.id) AS item_count
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN addresses a ON o.address_id = a.id
JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id, u.name, u.email, a.city;

-- Refresh periodically
REFRESH MATERIALIZED VIEW order_summaries;
```

## Index Optimization

### Index Types

```sql
-- B-tree (default, good for most cases)
CREATE INDEX idx_users_email ON users(email);

-- Composite index (order matters!)
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at DESC);

-- Partial index (for filtered queries)
CREATE INDEX idx_active_users ON users(email) WHERE status = 'active';

-- Expression index
CREATE INDEX idx_users_lower_email ON users(LOWER(email));

-- GIN index (for arrays, JSONB)
CREATE INDEX idx_products_tags ON products USING GIN(tags);

-- BRIN index (for large tables with natural ordering)
CREATE INDEX idx_logs_timestamp ON logs USING BRIN(created_at);
```

### Index Guidelines

```markdown
## When to Add Indexes
- [ ] Columns in WHERE clauses
- [ ] Columns in JOIN conditions
- [ ] Columns in ORDER BY
- [ ] Foreign keys
- [ ] Columns with high selectivity

## When NOT to Add Indexes
- [ ] Small tables (< 1000 rows)
- [ ] Columns with low selectivity (boolean, status)
- [ ] Tables with heavy write operations
- [ ] Frequently updated columns
```

## Query Optimization

### EXPLAIN ANALYZE

```sql
EXPLAIN ANALYZE
SELECT u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.created_at > '2024-01-01'
GROUP BY u.id
ORDER BY order_count DESC
LIMIT 10;
```

### Common Optimizations

**1. Use appropriate JOINs**
```sql
-- Bad: Subquery for each row
SELECT *, (SELECT COUNT(*) FROM orders WHERE user_id = u.id)
FROM users u;

-- Good: Single JOIN
SELECT u.*, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id;
```

**2. Avoid SELECT ***
```sql
-- Bad
SELECT * FROM users WHERE id = 1;

-- Good
SELECT id, name, email FROM users WHERE id = 1;
```

**3. Use LIMIT for pagination**
```sql
-- Offset pagination (slow for large offsets)
SELECT * FROM products ORDER BY id LIMIT 20 OFFSET 10000;

-- Keyset pagination (faster)
SELECT * FROM products WHERE id > 10000 ORDER BY id LIMIT 20;
```

**4. Batch operations**
```sql
-- Bad: Individual inserts
INSERT INTO logs (message) VALUES ('log1');
INSERT INTO logs (message) VALUES ('log2');

-- Good: Batch insert
INSERT INTO logs (message) VALUES ('log1'), ('log2'), ('log3');
```

## Common Patterns

### Soft Delete

```sql
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP;

-- "Delete" a user
UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE id = 1;

-- Query active users only
SELECT * FROM users WHERE deleted_at IS NULL;

-- Create view for convenience
CREATE VIEW active_users AS
SELECT * FROM users WHERE deleted_at IS NULL;
```

### Audit Trail

```sql
CREATE TABLE audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(10) NOT NULL, -- INSERT, UPDATE, DELETE
    old_data JSONB,
    new_data JSONB,
    changed_by INTEGER REFERENCES users(id),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trigger function
CREATE OR REPLACE FUNCTION audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, record_id, action, new_data)
        VALUES (TG_TABLE_NAME, NEW.id, 'INSERT', to_jsonb(NEW));
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, record_id, action, old_data, new_data)
        VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', to_jsonb(OLD), to_jsonb(NEW));
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, record_id, action, old_data)
        VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', to_jsonb(OLD));
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### Full-Text Search

```sql
-- Add search column
ALTER TABLE products ADD COLUMN search_vector tsvector;

-- Update search vector
UPDATE products SET search_vector =
    setweight(to_tsvector('english', name), 'A') ||
    setweight(to_tsvector('english', description), 'B');

-- Create GIN index
CREATE INDEX idx_products_search ON products USING GIN(search_vector);

-- Search query
SELECT * FROM products
WHERE search_vector @@ plainto_tsquery('english', 'wireless headphones')
ORDER BY ts_rank(search_vector, plainto_tsquery('english', 'wireless headphones')) DESC;
```

## Performance Checklist

```markdown
## Schema Design
- [ ] Appropriate data types (don't use VARCHAR(255) for everything)
- [ ] Proper constraints (NOT NULL, UNIQUE, CHECK)
- [ ] Foreign keys with proper ON DELETE behavior
- [ ] UUID vs SERIAL for primary keys (consider use case)

## Indexes
- [ ] Primary key indexes exist
- [ ] Foreign keys are indexed
- [ ] Frequently queried columns indexed
- [ ] No unused indexes (check pg_stat_user_indexes)

## Queries
- [ ] No N+1 queries
- [ ] Appropriate use of JOINs vs subqueries
- [ ] LIMIT on unbounded queries
- [ ] EXPLAIN ANALYZE on slow queries

## Maintenance
- [ ] Regular VACUUM and ANALYZE
- [ ] Connection pooling configured
- [ ] Query timeouts set
- [ ] Slow query logging enabled
```

## Useful Queries

```sql
-- Find unused indexes
SELECT
    schemaname || '.' || relname AS table,
    indexrelname AS index,
    pg_size_pretty(pg_relation_size(i.indexrelid)) AS index_size,
    idx_scan AS index_scans
FROM pg_stat_user_indexes ui
JOIN pg_index i ON ui.indexrelid = i.indexrelid
WHERE idx_scan < 50
ORDER BY pg_relation_size(i.indexrelid) DESC;

-- Find slow queries (requires pg_stat_statements)
SELECT
    query,
    calls,
    mean_exec_time,
    total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Table sizes
SELECT
    relname AS table,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```
