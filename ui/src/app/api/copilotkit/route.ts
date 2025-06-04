import {
  CopilotRuntime,
  OpenAIAdapter,
  ExperimentalOllamaAdapter, // ollama adapter
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";

import { NextRequest } from "next/server";

// const serviceAdapter = new OpenAIAdapter();
// adapter definition
const serviceAdapter = new ExperimentalOllamaAdapter({
  model: process.env.OLLAMA_MODEL,
});
const runtime = new CopilotRuntime({
  remoteEndpoints: [
    {
      url: process.env.REMOTE_ACTION_URL || "http://localhost:8000/copilotkit",
    },
  ],
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};