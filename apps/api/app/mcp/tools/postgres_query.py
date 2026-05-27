class PostgresQueryTool:
    """Execute safe SQL queries against PostgreSQL via MCP interface."""

    name = "postgres_query"
    description = "Execute a SQL query against the PostgreSQL database"
    requires_approval_for_writes = True

    def get_info(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "requires_approval": self.requires_approval_for_writes,
        }

    async def execute(self, arguments: dict) -> dict:
        query = arguments.get("query", "")
        return self._mock_execute(query)

    def _mock_execute(self, query: str) -> dict:
        query_lower = query.lower()
        if "customer" in query_lower or "user" in query_lower:
            return {
                "columns": ["id", "name", "email", "created_at"],
                "rows": [
                    [1, "Alice Johnson", "alice@example.com", "2024-01-15"],
                    [2, "Bob Smith", "bob@example.com", "2024-01-20"],
                    [3, "Carol White", "carol@example.com", "2024-02-01"],
                ],
                "row_count": 3,
            }
        if "order" in query_lower:
            return {
                "columns": ["id", "customer_id", "amount", "status", "created_at"],
                "rows": [
                    [101, 1, 1250.00, "completed", "2024-03-01"],
                    [102, 2, 890.50, "pending", "2024-03-05"],
                ],
                "row_count": 2,
            }
        return {
            "columns": ["result"],
            "rows": [["Query executed successfully"]],
            "row_count": 1,
        }
