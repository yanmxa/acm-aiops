"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useCoAgent } from "@copilotkit/react-core";
import { State } from "../lib/agent_state";

export default function ModelTogglePanel() {
  const [open, setOpen] = useState(false);
  const [provider, setProvider] = useState("OpenAI");
  const [modelName, setModelName] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const panelWidth = 340;
  const collapsedWidth = 28;

  const { state: agentState, setState } = useCoAgent<State>({
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
      className="fixed top-20 right-0 z-50 max-h-[calc(100vh-6rem)] flex shadow-lg transition-all duration-300 ease-in-out overflow-hidden rounded-l-lg bg-white border border-gray-200"
      style={{
        width: open ? panelWidth : collapsedWidth,
      }}
    >
      {/* Toggle Strip */}
      <div
        className="w-7 flex items-center justify-center cursor-pointer bg-gray-300 hover:bg-gray-400 transition-colors duration-200"
        onClick={() => setOpen((prev) => !prev)}
        title={open ? "Hide panel" : "Show panel"}
      >
        <div className="h-8 w-6 text-gray-600 hover:text-gray-700 flex items-center justify-center transition-colors">
          {open ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </div>
      </div>

      {/* Panel */}
      {open && (
        <div className="w-[312px] flex flex-col h-full bg-white overflow-hidden">
          <div className="p-4 border-b border-gray-100">
            <div className="flex items-center space-x-2">
              <div className="w-6 h-6 bg-blue-500 rounded-md flex items-center justify-center">
                <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <h2 className="text-base font-semibold text-gray-900">Model Settings</h2>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1.5 text-gray-700">Provider</label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full px-3 py-2 rounded-md border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors text-sm"
              >
                <option>OpenAI</option>
                <option>Ollama</option>
                <option>Groq</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5 text-gray-700">Model Name</label>
              <input
                value={modelName}
                onChange={(e) => setModelName(e.target.value)}
                placeholder="e.g. gpt-4o"
                className="w-full px-3 py-2 rounded-md border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors text-sm placeholder-gray-400"
              />
            </div>

            <div>
              <label className="block text-sm font-medium mb-1.5 text-gray-700">API Key</label>
              <input
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter API key"
                className="w-full px-3 py-2 rounded-md border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors text-sm placeholder-gray-400"
              />
            </div>

            {submitted && (
              <div className="bg-green-50 border border-green-200 rounded-md p-3">
                <div className="text-xs text-green-800 space-y-1">
                  <div className="flex items-center space-x-2">
                    <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                    <span><strong>Provider:</strong> {provider}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                    <span><strong>Model:</strong> {modelName || "Default"}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="p-4 border-t border-gray-100">
            <button
              onClick={handleSubmit}
              className="w-full bg-blue-500 text-white font-medium py-2 rounded-md hover:bg-blue-600 transition-colors text-sm"
            >
              Apply
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
