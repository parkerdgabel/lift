# LIFT MCP Server Package

This package implements the Model Context Protocol (MCP) server for LIFT, enabling AI assistants to access workout data and tools.

## Architecture

```
lift/mcp/
├── __init__.py      # Package exports
├── server.py        # Main MCP server implementation
├── config.py        # Configuration management
├── schemas.py       # Pydantic schemas for MCP types
├── handlers.py      # Base handler classes
├── resources.py     # Resource handlers (read-only data)
└── tools.py         # Tool handlers (actions)
```

## Core Components

### Server (`server.py`)

The `MCPServer` class is the main entry point:
- Initializes MCP protocol server
- Registers all resource and tool handlers
- Manages server lifecycle
- Handles stdio transport

### Resources (`resources.py`)

Resources provide read-only access to data:
- `WorkoutResourceHandler`: Workout history and details
- `ExerciseResourceHandler`: Exercise library
- `StatsResourceHandler`: Training statistics

Each resource handler:
- Implements `can_handle(uri)` to claim URIs
- Implements `get_resource(uri)` to fetch data
- Implements `list_resources()` to advertise capabilities

### Tools (`tools.py`)

Tools provide actions/mutations:
- `SearchExercisesTool`: Search exercises
- `GetExerciseInfoTool`: Get exercise details
- `StartWorkoutTool`: Start workout session
- `LogBodyweightTool`: Log bodyweight

Each tool handler:
- Defines name, description, and input schema
- Validates inputs using Pydantic
- Executes action via service layer
- Returns formatted response

### Configuration (`config.py`)

Manages MCP server configuration:
- Default config at `~/.lift/mcp-server.json`
- Server settings (name, version, transport)
- Database path configuration
- Feature flags (readonly mode, etc.)
- Rate limiting settings

### Schemas (`schemas.py`)

Pydantic models for type safety:
- Input schemas for all tools
- Response schemas for resources
- Validation and serialization

### Handlers (`handlers.py`)

Base classes for extensibility:
- `BaseHandler`: Database connection management
- `ResourceHandler`: Resource interface
- `ToolHandler`: Tool interface
- Error handling utilities

## Adding New Resources

1. Create a new handler class in `resources.py`:

```python
class MyResourceHandler(ResourceHandler):
    def can_handle(self, uri: str) -> bool:
        return uri.startswith("lift://my-resource/")

    def get_resource(self, uri: str) -> dict[str, Any]:
        # Fetch and return data
        pass

    def list_resources(self) -> list[Resource]:
        # Return resource metadata
        pass
```

2. Add to `get_all_resource_handlers()` in `resources.py`

3. Update documentation

## Adding New Tools

1. Define input schema in `schemas.py`:

```python
class MyToolInput(BaseModel):
    param1: str = Field(..., description="First parameter")
    param2: int = Field(0, description="Optional parameter")
```

2. Create tool handler in `tools.py`:

```python
class MyTool(ToolHandler):
    def get_name(self) -> str:
        return "my_tool"

    def get_description(self) -> str:
        return "Does something useful"

    def get_input_schema(self) -> dict[str, Any]:
        return MyToolInput.model_json_schema()

    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        # Validate input
        input_data = MyToolInput(**arguments)

        # Execute action
        result = self.my_service.do_something(input_data.param1)

        # Return formatted response
        return format_success_response(result)
```

3. Add to `get_all_tool_handlers()` in `tools.py`

4. Update documentation

## Integration with Services

The MCP layer is a thin wrapper over existing LIFT services:

```python
# In tool handler
self.workout_service = WorkoutService(self.db)
result = self.workout_service.create_workout(workout_data)
```

No changes needed to core services. MCP handles:
- Request validation
- Response formatting
- Error handling
- Protocol compliance

## Error Handling

All errors are caught and formatted:

```python
try:
    result = some_operation()
    return format_success_response(result)
except Exception as e:
    logger.error(f"Error: {e}")
    return format_error_response(str(e))
```

Users see friendly error messages, detailed logs go to stderr.

## Testing

Test structure:
- `tests/mcp/test_resources.py` - Resource handler tests
- `tests/mcp/test_tools.py` - Tool handler tests
- `tests/mcp/test_server.py` - Server integration tests

Run tests:
```bash
pytest tests/mcp/
```

## CLI Integration

MCP commands in `lift/cli/mcp.py`:
- `lift mcp start` - Start server
- `lift mcp config` - Generate config
- `lift mcp info` - Show configuration
- `lift mcp capabilities` - List features
- `lift mcp setup` - Interactive setup

## Development Workflow

1. **Make changes** to handlers or schemas
2. **Test locally**: `lift mcp start`
3. **Test with Claude**: Configure Claude Desktop
4. **Write tests**: Add unit/integration tests
5. **Update docs**: Update MCP_SERVER.md
6. **Commit**: Follow conventional commits

## Performance Considerations

- Resource responses cached for 60s
- Database connections pooled
- Query optimization via indexes
- Rate limiting prevents abuse

## Security

- No network exposure (stdio only)
- Local database access only
- Rate limiting prevents DoS
- Read-only mode available
- Input validation on all tools

## Debugging

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

View logs in Claude Desktop developer console.

## References

- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP SDK Documentation](https://github.com/modelcontextprotocol/python-sdk)
- [LIFT Documentation](../../README.md)
