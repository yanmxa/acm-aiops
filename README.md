# Chatting with Advanced Cluster Management

This project enables natural language interaction with Red Hat Advanced Cluster Management (ACM).

It includes:

* **Backend**: An AI agent workflow integrated with `multicluster-mcp-server`
* **Frontend**: A web UI based on the AG-UI protocol, built with **CopilotKit**

---

## 🧠 Backend Setup

1. **Install dependencies**

   ```bash
   cd agent
   poetry install
   ```

2. **Start the server**

   ```bash
   poetry run main
   ```

> **Note**: Set `OPENAI_API_KEY` in `.env`.

---

## 💬 Frontend Setup

1. **Install dependencies**

   ```bash
   cd ui
   pnpm install
   ```

2. **Development mode**

   ```bash
   pnpm run dev
   ```

3. **Production mode**

   ```bash
   pnpm run build
   pnpm run start
   ```
