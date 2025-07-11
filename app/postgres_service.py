# -*- coding: utf-8 -*-
"""
PostgreSQL service for MCP server
Provides database operations and query functionality
"""

import asyncio
import asyncpg
import json
from datetime import datetime, date
from urllib.parse import quote_plus
from typing import Dict, List, Any, Optional, Union
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy import text, inspect
from app.config import POSTGRES_DB_CONFIG
from app.logger import get_logger

logger = get_logger(__name__)


class PostgreSQLService:
    """PostgreSQL service for MCP server operations"""
    
    def __init__(self):
        self.connection_pool: Optional[asyncpg.Pool] = None
        self.engine = None
        self.session_factory = None
        self._setup_connection()
    
    def _setup_connection(self):
        """Setup database connection configuration"""
        try:
            # Create connection string for asyncpg with proper URL encoding
            password_encoded = quote_plus(POSTGRES_DB_CONFIG['password'])
            self.connection_string = (
                f"postgresql://{POSTGRES_DB_CONFIG['user']}:"
                f"{password_encoded}@"
                f"{POSTGRES_DB_CONFIG['host']}:"
                f"{POSTGRES_DB_CONFIG['port']}/"
                f"{POSTGRES_DB_CONFIG['dbname']}"
            )
            
            # Create SQLAlchemy async engine for advanced operations
            self.engine = create_async_engine(
                f"postgresql+asyncpg://{POSTGRES_DB_CONFIG['user']}:"
                f"{password_encoded}@"
                f"{POSTGRES_DB_CONFIG['host']}:"
                f"{POSTGRES_DB_CONFIG['port']}/"
                f"{POSTGRES_DB_CONFIG['dbname']}",
                echo=False,
                future=True
            )
            
            self.session_factory = async_sessionmaker(
                self.engine, 
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("PostgreSQL service configuration completed")
            
        except Exception as e:
            logger.error(f"Failed to setup PostgreSQL connection: {e}")
            raise
    
    async def initialize_pool(self) -> bool:
        """Initialize connection pool"""
        try:
            self.connection_pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("PostgreSQL connection pool initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            return False
    
    async def close_pool(self):
        """Close connection pool"""
        if self.connection_pool:
            await self.connection_pool.close()
            logger.info("PostgreSQL connection pool closed")
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test database connection"""
        try:
            # Try to initialize pool if not exists
            if not self.connection_pool:
                pool_init = await self.initialize_pool()
                if not pool_init:
                    return {
                        "status": "failed",
                        "error": "Failed to initialize connection pool"
                    }
            
            async with self.connection_pool.acquire() as conn:
                result = await conn.fetch("SELECT version(), current_database(), current_user")
                version_info = result[0]
                
                return {
                    "status": "connected",
                    "version": version_info["version"],
                    "database": version_info["current_database"],
                    "user": version_info["current_user"],
                    "connection_info": {
                        "host": POSTGRES_DB_CONFIG["host"],
                        "port": POSTGRES_DB_CONFIG["port"],
                        "database": POSTGRES_DB_CONFIG["dbname"]
                    }
                }
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def execute_query(self, query: str, params: List[Any] = None) -> Dict[str, Any]:
        """Execute a SQL query and return results"""
        try:
            # Try to initialize pool if not exists
            if not self.connection_pool:
                pool_init = await self.initialize_pool()
                if not pool_init:
                    return {
                        "success": False,
                        "error": "Failed to initialize connection pool",
                        "query": query
                    }
            
            async with self.connection_pool.acquire() as conn:
                # Check if query is SELECT or other type
                query_type = query.strip().upper().split()[0]
                
                if query_type == "SELECT":
                    if params:
                        rows = await conn.fetch(query, *params)
                    else:
                        rows = await conn.fetch(query)
                    
                    # Convert rows to list of dictionaries with datetime handling
                    results = []
                    for row in rows:
                        row_dict = {}
                        for key, value in row.items():
                            if isinstance(value, (datetime, date)):
                                row_dict[key] = value.isoformat()
                            else:
                                row_dict[key] = value
                        results.append(row_dict)
                    
                    return {
                        "success": True,
                        "query_type": "SELECT",
                        "row_count": len(results),
                        "data": results,
                        "columns": list(rows[0].keys()) if rows else []
                    }
                else:
                    # For INSERT, UPDATE, DELETE, etc.
                    if params:
                        result = await conn.execute(query, *params)
                    else:
                        result = await conn.execute(query)
                    
                    return {
                        "success": True,
                        "query_type": query_type,
                        "affected_rows": result.split()[-1] if result else "0",
                        "message": f"Query executed successfully: {result}"
                    }
                    
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    async def get_database_schema(self) -> Dict[str, Any]:
        """Get database schema information"""
        try:
            if not self.connection_pool:
                await self.initialize_pool()
            
            async with self.connection_pool.acquire() as conn:
                # Get all tables
                tables_query = """
                SELECT 
                    schemaname,
                    tablename,
                    tableowner
                FROM pg_tables 
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY schemaname, tablename
                """
                tables = await conn.fetch(tables_query)
                
                schema_info = {"tables": {}}
                
                # Get columns for each table
                for table in tables:
                    schema_name = table["schemaname"]
                    table_name = table["tablename"]
                    
                    columns_query = """
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns
                    WHERE table_schema = $1 AND table_name = $2
                    ORDER BY ordinal_position
                    """
                    
                    columns = await conn.fetch(columns_query, schema_name, table_name)
                    
                    full_table_name = f"{schema_name}.{table_name}"
                    schema_info["tables"][full_table_name] = {
                        "schema": schema_name,
                        "table": table_name,
                        "owner": table["tableowner"],
                        "columns": [dict(col) for col in columns]
                    }
                
                return {
                    "success": True,
                    "database": POSTGRES_DB_CONFIG["dbname"],
                    "schema_count": len(set(t["schemaname"] for t in tables)),
                    "table_count": len(tables),
                    "schema": schema_info
                }
                
        except Exception as e:
            logger.error(f"Failed to get database schema: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_table_info(self, table_name: str, schema: str = "public") -> Dict[str, Any]:
        """Get detailed information about a specific table"""
        try:
            if not self.connection_pool:
                await self.initialize_pool()
            
            async with self.connection_pool.acquire() as conn:
                # Table basic info
                table_query = """
                SELECT 
                    schemaname,
                    tablename,
                    tableowner,
                    tablespace,
                    hasindexes,
                    hasrules,
                    hastriggers
                FROM pg_tables 
                WHERE schemaname = $1 AND tablename = $2
                """
                table_info = await conn.fetchrow(table_query, schema, table_name)
                
                if not table_info:
                    return {
                        "success": False,
                        "error": f"Table {schema}.{table_name} not found"
                    }
                
                # Column information
                columns_query = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns
                WHERE table_schema = $1 AND table_name = $2
                ORDER BY ordinal_position
                """
                columns = await conn.fetch(columns_query, schema, table_name)
                
                # Index information
                indexes_query = """
                SELECT 
                    indexname,
                    indexdef
                FROM pg_indexes
                WHERE schemaname = $1 AND tablename = $2
                """
                indexes = await conn.fetch(indexes_query, schema, table_name)
                
                # Row count
                count_query = f'SELECT COUNT(*) as row_count FROM "{schema}"."{table_name}"'
                row_count = await conn.fetchrow(count_query)
                
                return {
                    "success": True,
                    "table_info": dict(table_info),
                    "columns": [dict(col) for col in columns],
                    "indexes": [dict(idx) for idx in indexes],
                    "row_count": row_count["row_count"]
                }
                
        except Exception as e:
            logger.error(f"Failed to get table info for {schema}.{table_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_query_performance(self, query: str) -> Dict[str, Any]:
        """Analyze query performance using EXPLAIN"""
        try:
            if not self.connection_pool:
                await self.initialize_pool()
            
            async with self.connection_pool.acquire() as conn:
                # Get query plan
                explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
                result = await conn.fetchrow(explain_query)
                
                plan_data = result[0]
                
                return {
                    "success": True,
                    "query": query,
                    "execution_plan": plan_data,
                    "analysis": self._extract_performance_metrics(plan_data)
                }
                
        except Exception as e:
            logger.error(f"Query performance analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    def _extract_performance_metrics(self, plan_data: List[Dict]) -> Dict[str, Any]:
        """Extract key performance metrics from execution plan"""
        try:
            plan = plan_data[0]["Plan"]
            
            return {
                "total_cost": plan.get("Total Cost", 0),
                "startup_cost": plan.get("Startup Cost", 0),
                "actual_time": plan.get("Actual Total Time", 0),
                "rows": plan.get("Actual Rows", 0),
                "node_type": plan.get("Node Type", "Unknown"),
                "shared_hit_blocks": plan.get("Shared Hit Blocks", 0),
                "shared_read_blocks": plan.get("Shared Read Blocks", 0),
                "temp_read_blocks": plan.get("Temp Read Blocks", 0),
                "temp_written_blocks": plan.get("Temp Written Blocks", 0)
            }
        except Exception as e:
            logger.error(f"Failed to extract performance metrics: {e}")
            return {"error": str(e)}

    async def get_database_size_info(self) -> Dict[str, Any]:
        """Get detailed database size information"""
        try:
            if not self.connection_pool:
                await self.initialize_pool()
            
            async with self.connection_pool.acquire() as conn:
                # Get database size
                size_query = """
                SELECT 
                    pg_database.datname as database_name,
                    pg_size_pretty(pg_database_size(pg_database.datname)) as size_pretty,
                    pg_database_size(pg_database.datname) as size_bytes
                FROM pg_database 
                WHERE pg_database.datname = current_database()
                """
                
                # Get table sizes
                tables_query = """
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
                    pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) as indexes_size,
                    pg_total_relation_size(schemaname||'.'||tablename) as total_bytes
                FROM pg_tables
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 10
                """
                
                db_info = await conn.fetchrow(size_query)
                tables_info = await conn.fetch(tables_query)
                
                return {
                    "success": True,
                    "database": dict(db_info) if db_info else {},
                    "largest_tables": [dict(table) for table in tables_info]
                }
                
        except Exception as e:
            logger.error(f"Failed to get database size info: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_slow_queries(self, limit: int = 10) -> Dict[str, Any]:
        """Get slow queries from pg_stat_statements (if extension is available)"""
        try:
            if not self.connection_pool:
                await self.initialize_pool()
            
            async with self.connection_pool.acquire() as conn:
                # Check if pg_stat_statements extension is available
                check_query = """
                SELECT EXISTS (
                    SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
                ) as has_extension
                """
                
                check_result = await conn.fetchrow(check_query)
                
                if not check_result["has_extension"]:
                    return {
                        "success": False,
                        "error": "pg_stat_statements extension not available"
                    }
                
                # Get slow queries
                slow_query = f"""
                SELECT 
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    max_exec_time,
                    stddev_exec_time,
                    rows,
                    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                FROM pg_stat_statements
                ORDER BY mean_exec_time DESC
                LIMIT {limit}
                """
                
                queries = await conn.fetch(slow_query)
                
                return {
                    "success": True,
                    "slow_queries": [dict(query) for query in queries]
                }
                
        except Exception as e:
            logger.error(f"Failed to get slow queries: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def optimize_table(self, table_name: str, schema: str = "public") -> Dict[str, Any]:
        """Optimize table by running VACUUM and ANALYZE"""
        try:
            if not self.connection_pool:
                await self.initialize_pool()
            
            async with self.connection_pool.acquire() as conn:
                # VACUUM and ANALYZE
                vacuum_query = f'VACUUM ANALYZE "{schema}"."{table_name}"'
                await conn.execute(vacuum_query)
                
                # Get table statistics after optimization
                stats_query = f"""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                WHERE schemaname = $1 AND tablename = $2
                """
                
                stats = await conn.fetchrow(stats_query, schema, table_name)
                
                return {
                    "success": True,
                    "message": f"Table {schema}.{table_name} optimized successfully",
                    "statistics": dict(stats) if stats else {}
                }
                
        except Exception as e:
            logger.error(f"Failed to optimize table {schema}.{table_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_locks_info(self) -> Dict[str, Any]:
        """Get information about database locks"""
        try:
            if not self.connection_pool:
                await self.initialize_pool()
            
            async with self.connection_pool.acquire() as conn:
                locks_query = """
                SELECT 
                    pg_locks.locktype,
                    pg_locks.database,
                    pg_locks.relation,
                    pg_locks.page,
                    pg_locks.tuple,
                    pg_locks.classid,
                    pg_locks.objid,
                    pg_locks.objsubid,
                    pg_locks.pid,
                    pg_locks.mode,
                    pg_locks.granted,
                    pg_stat_activity.usename,
                    pg_stat_activity.query,
                    pg_stat_activity.query_start
                FROM pg_locks
                JOIN pg_stat_activity ON pg_locks.pid = pg_stat_activity.pid
                WHERE pg_stat_activity.pid != pg_backend_pid()
                ORDER BY pg_locks.granted, pg_locks.pid
                """
                
                locks = await conn.fetch(locks_query)
                
                return {
                    "success": True,
                    "locks_count": len(locks),
                    "locks": [dict(lock) for lock in locks]
                }
                
        except Exception as e:
            logger.error(f"Failed to get locks info: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global PostgreSQL service instance
postgres_service = PostgreSQLService()
