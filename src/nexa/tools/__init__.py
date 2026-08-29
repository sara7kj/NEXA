from nexa.tools.executor import execute_tool, registry
from nexa.tools.projects import GET_PROJECT_DETAILS, QUERY_PROJECTS
from nexa.tools.update_status import UPDATE_PROJECT_STATUS

registry.register(QUERY_PROJECTS)
registry.register(GET_PROJECT_DETAILS)
registry.register(UPDATE_PROJECT_STATUS)

__all__ = ["execute_tool", "registry"]