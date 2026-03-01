"""
SQLite-compatible data layer for Chainlit.

Chainlit's SQLAlchemyDataLayer uses "ORDER BY ... NULLS LAST", which older
SQLite versions do not support. This subclass rewrites queries to remove
NULLS FIRST/NULLS LAST before execution.
"""

from typing import Any, Dict, List, Union

from chainlit.data.sql_alchemy import SQLAlchemyDataLayer


class SQLiteCompatibleDataLayer(SQLAlchemyDataLayer):
    """SQLAlchemyDataLayer with SQLite-compatible SQL (strips NULLS FIRST/LAST)."""

    async def execute_sql(
        self, query: str, parameters: dict
    ) -> Union[List[Dict[str, Any]], int, None]:
        # SQLite < 3.30 does not support NULLS FIRST / NULLS LAST
        query = query.replace(" NULLS LAST", "").replace(" NULLS FIRST", "")
        return await super().execute_sql(query, parameters)
