from .control_plane import health_snapshot

def system_health(marketplaces, state):
    executions=len(state.revenue_attempts)+len(state.marketplace_tasks)
    failures=sum(1 for x in state.revenue_attempts if x.get("status") in ("failed","cancelled"))
    return health_snapshot(marketplaces, executions, failures)
