class MCPInterface:
    """MCP-ready tool abstraction. Can be replaced by real MCP SDK clients."""

    def __init__(self) -> None:
        self._tools: dict[str, object] = {}

    def register_tool(self, name: str, tool: object) -> None:
        self._tools[name] = tool

    async def list_tools(self) -> list[dict]:
        return [tool.get_info() for tool in self._tools.values()]

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        if tool_name not in self._tools:
            raise ValueError(f"Tool {tool_name} not found")
        return await self._tools[tool_name].execute(arguments)
