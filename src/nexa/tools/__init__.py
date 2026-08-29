from nexa.tools.executor import execute_tool, registry
from nexa.tools.projects import GET_PROJECT_DETAILS, QUERY_PROJECTS

registry.register(QUERY_PROJECTS)
registry.register(GET_PROJECT_DETAILS)

__all__ = ["execute_tool", "registry"]