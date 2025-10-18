from datetime import datetime
from typing import Optional

from moose_lib import ConsumptionApi, EgressConfig
from pydantic import BaseModel


class MooseHealthQuery(BaseModel):
    pass


class MooseHealthResponse(BaseModel):
    status: str
    checked_at: datetime
    details: Optional[str] = None


def get_moose_health(client, params: MooseHealthQuery) -> MooseHealthResponse:
    try:
        client.query.execute("SELECT 1")
        return MooseHealthResponse(status="ok", checked_at=datetime.utcnow())
    except Exception as exc:
        return MooseHealthResponse(
            status="error",
            checked_at=datetime.utcnow(),
            details=str(exc),
        )


get_moose_health_api = ConsumptionApi[MooseHealthQuery, MooseHealthResponse](
    "getMooseHealth",
    query_function=get_moose_health,
    source="moose_health",
    config=EgressConfig(),
)
