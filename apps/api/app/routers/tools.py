from fastapi import APIRouter, Depends

from app.core.deps import get_current_active_user
from app.gateway.tool_gateway import tool_gateway
from app.models.user import User
from app.schemas.tool import ToolInfo, ToolListResponse

router = APIRouter()


@router.get("", response_model=ToolListResponse)
async def list_tools(current_user: User = Depends(get_current_active_user)) -> ToolListResponse:
    tools = [ToolInfo(**tool) for tool in await tool_gateway.list_tools()]
    return ToolListResponse(tools=tools)
