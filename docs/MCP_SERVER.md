# LIFT MCP Server

The LIFT MCP (Model Context Protocol) Server enables AI assistants like Claude to interact with your workout tracking data, providing intelligent coaching, analysis, and recommendations based on your actual training history.

## What is MCP?

Model Context Protocol (MCP) is an open protocol that allows AI assistants to securely access external data sources and tools. The LIFT MCP server exposes your workout data and tracking capabilities to Claude Desktop and other MCP clients.

## Features

### Resources (Read-Only Access)
- **Workout Data**: Access recent workouts, workout history, and detailed session information
- **Exercise Library**: Search and browse 137+ exercises with detailed information
- **Statistics**: View training summaries, progression data, and performance metrics
- **Body Tracking**: Access bodyweight trends and measurement history

### Tools (Actions)
- **Search Exercises**: Find exercises by name, muscle group, category, or equipment
- **Get Exercise Info**: Retrieve detailed information about specific exercises
- **Start Workout**: Begin a new workout session
- **Log Bodyweight**: Record bodyweight measurements

### Coming Soon
- Log workout sets during sessions
- Analyze exercise progression
- View personal records
- Volume analysis by muscle group
- Program management

## Installation

### Prerequisites

1. **Install LIFT with MCP support**:
   ```bash
   pip install lift[mcp]
   ```

2. **Install Claude Desktop**:
   - Download from [https://claude.ai/download](https://claude.ai/download)

### Quick Setup

Use the interactive setup wizard:

```bash
lift mcp setup
```

This will guide you through configuring Claude Desktop to use LIFT.

### Manual Setup

1. **Generate MCP configuration**:
   ```bash
   lift mcp config > temp_config.json
   ```

2. **Locate Claude Desktop config file**:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

3. **Add LIFT to Claude Desktop config**:

   Open (or create) the Claude Desktop config file and add the `mcpServers` section:

   ```json
   {
     "mcpServers": {
       "lift": {
         "command": "/path/to/lift",
         "args": ["mcp", "start"],
         "description": "LIFT workout tracker"
       }
     }
   }
   ```

   Replace `/path/to/lift` with the actual path to your `lift` command.

4. **Restart Claude Desktop**

5. **Verify connection**:
   - Look for the MCP server icon in Claude Desktop
   - Ask Claude: "Can you access my LIFT workout data?"

## Usage Examples

### Getting Started

Once connected, you can interact with your workout data naturally:

```
You: "Show me my recent workouts"

Claude: [Uses lift://workouts/recent resource]
"Here are your last 10 workouts..."
```

```
You: "What exercises target chest?"

Claude: [Uses search_exercises tool]
"Here are the chest exercises available..."
```

### Workout Planning

```
You: "I want to train chest and triceps today. What exercises should I do?"

Claude: [Searches exercises, reviews your history]
"Based on your training history, I recommend:
1. Barbell Bench Press - you last did 185lbs x 10
2. Incline Dumbbell Press
3. Cable Flyes
4. Tricep Pushdowns..."
```

### Performance Analysis

```
You: "How is my bench press progressing?"

Claude: [Accesses workout history and progression data]
"Your bench press has improved significantly:
- 4 weeks ago: 175lbs x 10
- 2 weeks ago: 180lbs x 10
- Last workout: 185lbs x 10
You're adding 5lbs every 2 weeks - excellent progressive overload!"
```

### Workout Logging

```
You: "Start a new workout called 'Push Day'"

Claude: [Uses start_workout tool]
"Workout started! ID: 42. Ready to log your sets."

You: "Log 185lbs x 10 reps on bench press at RPE 8"

Claude: [Uses log_workout_set tool - coming soon]
"Set logged! That matches your PR from last week."
```

### Body Tracking

```
You: "Log my weight at 185 lbs"

Claude: [Uses log_bodyweight tool]
"Bodyweight logged: 185 lbs. That's down 2 lbs from last week."
```

## Configuration

### View Current Configuration

```bash
lift mcp info
```

### Configuration File

Location: `~/.lift/mcp-server.json`

```json
{
  "server": {
    "name": "lift-mcp-server",
    "version": "0.1.0",
    "transport": "stdio"
  },
  "database": {
    "path": "~/.lift/lift.duckdb"
  },
  "features": {
    "enable_workout_logging": true,
    "enable_program_management": true,
    "enable_body_tracking": true,
    "readonly_mode": false
  },
  "rate_limiting": {
    "enabled": true,
    "max_requests_per_minute": 60
  }
}
```

### Read-Only Mode

To prevent accidental modifications:

1. Edit `~/.lift/mcp-server.json`
2. Set `"readonly_mode": true` under `features`
3. Restart the MCP server

In read-only mode, tools that modify data will be disabled.

## Available Capabilities

### Resources

| URI Pattern | Description |
|-------------|-------------|
| `lift://workouts/recent` | Last 10 completed workouts |
| `lift://workouts/{id}` | Specific workout details |
| `lift://exercises/library` | Complete exercise library (137+ exercises) |
| `lift://stats/summary?period=week` | Weekly training summary |
| `lift://stats/summary?period=month` | Monthly training summary |

### Tools

| Tool Name | Description | Status |
|-----------|-------------|---------|
| `search_exercises` | Search exercises by criteria | ✅ Available |
| `get_exercise_info` | Get detailed exercise information | ✅ Available |
| `start_workout` | Start a new workout session | ✅ Available |
| `log_bodyweight` | Log bodyweight measurement | ✅ Available |
| `log_workout_set` | Log a set during workout | 🚧 Coming soon |
| `finish_workout` | Complete workout session | 🚧 Coming soon |
| `get_personal_records` | View PRs for exercises | 🚧 Coming soon |
| `analyze_volume` | Analyze training volume | 🚧 Coming soon |

## Troubleshooting

### Claude Can't See LIFT

**Problem**: Claude says it can't access LIFT data

**Solutions**:
1. Verify MCP server is configured in Claude Desktop config
2. Check the `lift` command path is correct
3. Restart Claude Desktop
4. Check server logs: `lift mcp info`

### Permission Errors

**Problem**: MCP server fails to start with permission errors

**Solutions**:
1. Check database file permissions: `ls -l ~/.lift/lift.duckdb`
2. Ensure database directory exists: `mkdir -p ~/.lift`
3. Initialize database if needed: `lift init`

### Tools Not Working

**Problem**: Claude can list resources but tools don't work

**Solutions**:
1. Check `readonly_mode` is set to `false`
2. Verify database is initialized: `lift info`
3. Check MCP server logs for errors

### Connection Issues

**Problem**: MCP server starts but Claude can't connect

**Solutions**:
1. Verify stdio transport is configured (default)
2. Check no other process is using the database
3. Try restarting Claude Desktop
4. Check Claude Desktop developer console for errors

## Security Considerations

### Data Privacy

- All data stays local on your machine
- No data is sent to external servers
- MCP protocol uses stdio (standard input/output) for local communication
- Database file permissions control access

### Rate Limiting

The MCP server includes rate limiting (60 requests/minute by default) to prevent:
- Accidental loops
- Resource exhaustion
- Unintended data modifications

### Read-Only Mode

Use read-only mode when:
- You want analysis only
- Testing with a new MCP client
- Sharing access with others
- Debugging issues

## Performance

### Resource Usage

- Minimal CPU usage when idle
- Database queries optimized with indexes
- Resources are cached for 60 seconds
- Connection pooling for concurrent requests

### Response Times

Typical response times:
- Resource reads: < 100ms
- Exercise searches: < 50ms
- Tool executions: < 200ms
- Complex analytics: < 500ms

## Development

### Testing the MCP Server

```bash
# Start server in foreground
lift mcp start

# Test with MCP Inspector (if available)
mcp-inspector test lift://workouts/recent

# Check server capabilities
lift mcp capabilities
```

### Logs

MCP server logs to stderr (visible in Claude Desktop developer console):

```bash
# View logs in Claude Desktop
# Developer > Toggle Developer Tools > Console tab
```

## Support

### Getting Help

- Documentation: [GitHub README](https://github.com/parkerdgabel/lift)
- Issues: [GitHub Issues](https://github.com/parkerdgabel/lift/issues)
- Examples: [docs/MCP_EXAMPLES.md](MCP_EXAMPLES.md)

### Reporting Bugs

When reporting MCP issues, include:
1. LIFT version: `lift version`
2. MCP config: `lift mcp info`
3. Error messages from Claude Desktop console
4. Steps to reproduce

## Roadmap

### Phase 2 (v0.2.0)
- Complete workout logging workflow
- PR detection and analysis
- Volume analytics
- Exercise progression tracking

### Phase 3 (v0.3.0)
- Program management tools
- Workout recommendations
- Recovery tracking
- Advanced analytics

### Phase 4 (v0.4.0)
- Multi-user support
- SSE transport for web clients
- Real-time notifications
- Mobile app integration

## Learn More

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Claude Desktop Documentation](https://claude.ai/docs)
- [LIFT Documentation](../README.md)

---

**Made with Claude Code** 🤖
