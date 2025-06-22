"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useCoAgent } from "@copilotkit/react-core";
import { AgentState } from "../lib/agent_state";

export default function ModelTogglePanel() {
  const [open, setOpen] = useState(false);
  const [provider, setProvider] = useState("OpenAI");
  const [modelName, setModelName] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const panelWidth = 340;
  const collapsedWidth = 28;

  const { state: agentState, setState } = useCoAgent<AgentState>({
    name: "chat_agent",
  });

  const handleSubmit = () => {
    // agentState.modelConfig = { provider, modelName, apiKey };
    setState(agentState);
    setSubmitted(true);
    // console.log("✅ Model set:", agentState.modelConfig);
  };

  return (
    <div
      className="fixed top-24 right-0 z-50 h-[22rem] flex shadow-lg transition-all duration-300 ease-in-out overflow-hidden rounded-l-xl border-l border-gray-200"
      style={{
        width: open ? panelWidth : collapsedWidth,
        backgroundColor: open ? "#f8f9fa" : "#e2e8f0",
      }}
    >
      {/* Toggle Strip */}
      <div
        className="w-7 flex items-center justify-center cursor-pointer hover:bg-gray-300 transition"
        onClick={() => setOpen((prev) => !prev)}
        title={open ? "Hide panel" : "Show panel"}
      >
        <div className="h-10 w-6 text-gray-600 flex items-center justify-center">
          {open ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </div>
      </div>

      {/* Panel */}
      {open && (
        <div className="p-4 w-[312px] flex flex-col justify-between text-sm text-gray-800">
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">Model Configuration</h2>

            <div>
              <label className="block text-xs font-medium mb-1">Model Provider</label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full px-3 py-1.5 rounded border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-red-500 text-sm"
              >
                <option>OpenAI</option>
                <option>Ollama</option>
                <option>Groq</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium mb-1">Model Name</label>
              <input
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                placeholder="e.g. gpt-4o"
                className="w-full px-3 py-1.5 rounded border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-red-500 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-medium mb-1">API Key</label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter API key"
                className="w-full px-3 py-1.5 rounded border border-gray-300 bg-white focus:outline-none focus:ring-2 focus:ring-red-500 text-sm"
              />
            </div>
          </div>

          <div className="mt-4">
            <button
              onClick={handleSubmit}
              className="w-full bg-red-600 text-white font-medium py-2 rounded-md hover:bg-red-700 transition text-sm"
            >
              Apply
            </button>

            {submitted && (
              <div className="mt-3 border-t pt-2 text-xs text-gray-600">
                <div><strong>Provider:</strong> {provider}</div>
                <div><strong>Model:</strong> {modelName}</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
