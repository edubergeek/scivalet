# Integration & MCP Guidelines

## Database Integration: MariaDB (via MCP-Alchemy)

This project leverages the Model Context Protocol (MCP) to allow Antigravity autonomous agents to safely discover schemas, inspect constraints, and interact with the MariaDB data layer natively.

## Connection Architecture
- **Protocol**: Model Context Protocol (MCP) using `stdio` transport
- **Driver Layer**: SQLAlchemy abstracted via `mcp-alchemy`
- **Native Driver**: `mariadb-connector-python`

## Configuration File (`mcp_config.json`)

## Enabled MCP Servers
You have access to the following MCP servers configured in `mcp_config.json`. Use them under these exact conditions:
* **MariaDB:** Use mariadb for local persistent storage of tabular data, user authentication, and backend routing.
  * *Trigger:* When data metrics or catalog schemas are required for the application logic.
  * *Trigger:* When a task involves database read/writes or user session management.
* **Composio / GitHub MCP:** Use this for source control and PR management.
  * *Trigger:* When an Implementation Plan is complete, trigger a commit  the `develop` branch and open a PR.
* **SQLAlchemy:** Use SQLAlchemy to model persistent data for the MariaDB backend.
* **Harvard ADS:** Use the [Harvard ADS](https://ui.adsabs.harvard.edu/) system to scan for publications by name or ORCID.
* **Google Scholar:** Use [Google Search](https://scholar.google.com/) to scan for publications by name or ORCID.

## Agent-Facing Capabilities
When this integration is active, the Antigravity agent has autonomous access to the following structural tools:
- `list_tables`: Scans and lists all schemas available in the targeted MariaDB instance.
- `describe_table`: Fetches columns, data types, primary keys, and foreign key relationships.
- `execute_query`: Runs arbitrary SQL blocks (used heavily during agent planning and context gathering).

## ⚠️ Safe Usage and Vibe Coding Rules
1. **Context Engineering First**: When initiating a task involving database migrations, model adjustments, or query building, always inspect the current database schema using mariadb_alchemy before generating code.
2. **Execution Permissions**: Always `request review` for terminal/query execution to prevent accidental data modifications or destructive structural migrations during autonomous code loops.

## Account Access Strategy
* Assume the environment holds the necessary OAuth tokens.
* If an MCP tool returns an "Unauthorized" error, halt execution and prompt the user to refresh their connection in the AntiGravity Customizations tab.

