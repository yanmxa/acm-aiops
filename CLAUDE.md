# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend (Python Agent)
```bash
# Install dependencies
cd agent && uv sync

# Start the backend server
uv run main

# Run with development dependencies
uv sync --extra dev
```

### Frontend (Next.js UI)
```bash
# Install dependencies
cd ui && pnpm install

# Development server with Turbopack
pnpm run dev

# Production build and start
pnpm run build
pnpm run start

# Linting
pnpm run lint
```

## Architecture Overview

This project implements a **federated learning monitoring system** with natural language interaction capabilities for Red Hat Advanced Cluster Management (ACM).

### Key Components

**Backend (`/agent`):**
- **FastAPI** server with **Enhanced Streaming Protocol**
- **LangGraph** workflow engine for AI agent orchestration
- **Enhanced streaming implementation** with real-time event emission
- **Federated monitoring workflow** with specialized nodes:
  - `inspector`: Analyzes user queries and determines data requirements
  - `analyzer`: Processes metrics and creates analysis
  - `chart`: Handles visualization generation using `render_recharts`
  - `prometheus`: Executes MCP tools for Prometheus queries
- **MCP (Model Context Protocol)** integration via `multicluster-mcp-server`
- Model factory supporting both **OpenAI** and **Groq** providers
- **Protocol compatibility** maintaining CopilotKit frontend interface

**Frontend (`/ui`):**
- **Next.js 15** with App Router
- **CopilotKit React** components for AI chat interface
- **AG-UI protocol** implementation
- **Recharts** for data visualization
- **TailwindCSS** for styling
- **React Flow** for workflow visualization

### State Management
- LangGraph `State` object manages workflow context
- `MemorySaver` provides conversation persistence
- State includes messages, query context, and tool results

### Tool Integration
- MCP tools for Kubernetes cluster interaction
- Prometheus metrics querying capabilities
- Chart rendering with Recharts integration
- Dynamic tool loading via `sync_get_mcp_tools`

## Environment Configuration

Required environment variables:
- `OPENAI_API_KEY` or `GROQ_API_KEY` for AI models
- `YEKA_OPENAI_API_KEY` and `YEKA_OPENAI_BASE_URL` for custom OpenAI endpoints
- `USE_GROQ=true` to switch to Groq provider
- `REMOTE_ACTION_URL` for backend API endpoint (defaults to `http://localhost:8000/copilotkit`)

## Testing and Development

- Backend uses **pytest** for testing (in dev dependencies)
- Frontend follows Next.js testing conventions
- Jupyter notebooks in `/agent/src/notebooks/` for workflow exploration
- Development server supports hot reloading for both frontend and backend