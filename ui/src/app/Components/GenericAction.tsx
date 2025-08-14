"use client";

import React, { useState, useEffect } from "react";
import { CheckCircle, Hammer } from "lucide-react";

type GenericActionProps = {
  status: "complete" | "executing";
  args: Record<string, unknown>;
  name: string;
  result?: string | Record<string, unknown>;
};

// Simple tool icon - just show hammer icon for all tools
const getToolIcon = () => {
  return <Hammer className="w-4 h-4" />;
};

export const GenericAction = ({
  args,
  name,
  result,
}: GenericActionProps) => {
  // State for preserving the last valid result and label
  const [lastValidResult, setLastValidResult] = useState<string | Record<string, unknown> | undefined>(result);
  const [lastValidLabel, setLastValidLabel] = useState<string>(name);
  const [isExpanded, setIsExpanded] = useState(false);

  // Helper function to check if a result is valid (not empty)
  const isValidResult = (value: string | Record<string, unknown> | undefined): boolean => {
    if (!value) return false;
    if (typeof value === 'string') return value !== "";
    if (typeof value === 'object') return Object.keys(value).length > 0;
    return Boolean(value);
  };

  // Helper function to format result for display
  const formatResultForDisplay = (rawResult: string | Record<string, unknown> | undefined): string => {
    if (!rawResult) return "";
    
    // If rawResult is already an object (not a string), stringify it directly
    if (typeof rawResult === 'object') {
      return JSON.stringify(rawResult, null, 2);
    }
    
    try {
      // Try to parse as JSON object for pretty formatting
      const parsed = JSON.parse(String(rawResult));
      return JSON.stringify(parsed, null, 2);
    } catch {
      // If not JSON, return as string
      return String(rawResult);
    }
  };

  // Update preserved result and label only when we receive a new valid result
  useEffect(() => {
    if (isValidResult(result)) {
      setLastValidResult(result);
      setLastValidLabel(name);
    }
  }, [result, name]);

  // console.log(`Action "${name}":`, { status, args, result, lastValidResult });

  return (
    <div className="w-full py-2 px-6">
      <div className="bg-white border border-gray-200 shadow-sm rounded-lg p-3">
        {/* Action Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-3">
            {/* Tool Icon */}
            <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-slate-50 to-slate-100 rounded-lg flex items-center justify-center text-slate-600">
              {getToolIcon()}
            </div>
            
            {/* Action Name */}
            <div className="text-sm font-medium text-slate-800">
              {args?.cluster && args.cluster !== "default" ? (
                <>
                  <span className="text-blue-600 font-medium">{args.cluster}</span>
                  <span className="text-slate-400 mx-1.5">•</span>
                  <span>{lastValidLabel}</span>
                </>
              ) : (
                lastValidLabel
              )}
            </div>
          </div>
          
          {/* Toggle button */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center space-x-1 text-xs text-slate-500 hover:text-slate-700 transition-colors px-2 py-1 rounded-md hover:bg-slate-50"
            >
              <span>{isExpanded ? "Hide details" : "Show details"}</span>
            </button>
            
            <div className="flex-shrink-0 w-6 h-6 bg-slate-100 hover:bg-slate-200 rounded-md flex items-center justify-center transition-colors cursor-pointer"
                 onClick={() => setIsExpanded(!isExpanded)}>
              <span className="text-xs text-slate-500 hover:text-slate-700 transition-colors">
                {isExpanded ? "▲" : "▼"}
              </span>
            </div>
          </div>
        </div>

      {/* Action Details (Collapsible) - integrated into the same panel */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          {/* Input Section */}
          <div className="mb-4">
            <div className="bg-gradient-to-r from-slate-50 to-slate-100 px-3 py-2 rounded-t-md">
              <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wide flex items-center gap-2">
                <Hammer className="w-3 h-3" />
                Input Parameters
              </h4>
            </div>
            <div className="bg-slate-50 p-3 rounded-b-md border border-slate-200">
              {/* Special handling for kubectl with yaml */}
              {name === "kubectl" && args?.yaml && typeof args.yaml === "string" && args.yaml.trim() ? (
                <div className="space-y-4">
                  {/* Show command if exists */}
                  {args?.command && (
                    <div>
                      <div className="text-xs font-semibold text-slate-700 mb-2 flex items-center gap-1">
                        <span className="w-1 h-1 bg-blue-500 rounded-full"></span>
                        Command
                      </div>
                      <div className="bg-gradient-to-r from-slate-800 to-slate-700 rounded-lg p-3 shadow-sm">
                        <code className="text-xs text-green-400 font-mono block">{String(args?.command || '')}</code>
                      </div>
                    </div>
                  )}
                  {/* Show YAML content */}
                  <div>
                    <div className="text-xs font-semibold text-slate-700 mb-2 flex items-center gap-1">
                      <span className="w-1 h-1 bg-emerald-500 rounded-full"></span>
                      YAML Configuration
                    </div>
                    <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg p-4 shadow-lg">
                      <pre className="text-xs overflow-auto font-mono leading-relaxed">
                        <code className="language-yaml text-slate-200">{args.yaml}</code>
                      </pre>
                    </div>
                  </div>
                  {/* Show other parameters if any */}
                  {Object.keys(args).some(key => key !== 'yaml' && key !== 'command') && (
                    <div>
                      <div className="text-xs font-semibold text-slate-700 mb-2 flex items-center gap-1">
                        <span className="w-1 h-1 bg-orange-500 rounded-full"></span>
                        Additional Parameters
                      </div>
                      <div className="bg-gradient-to-r from-slate-800 to-slate-700 rounded-lg p-3 shadow-sm">
                        <code className="text-xs text-slate-300 font-mono block whitespace-pre">{JSON.stringify(
                          Object.fromEntries(
                            Object.entries(args).filter(([key]) => key !== 'yaml' && key !== 'command')
                          ), 
                          null, 
                          2
                        )}</code>
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                /* Default JSON display for other tools */
                <pre className="text-xs overflow-auto text-slate-700 font-mono">
                  <code>{JSON.stringify(args, null, 2)}</code>
                </pre>
              )}
            </div>
          </div>

          {/* Output Section (only show if we have a result) */}
          {isValidResult(lastValidResult) && (
            <div>
              <div className="bg-gradient-to-r from-emerald-50 to-emerald-100 px-3 py-2 rounded-t-md">
                <h4 className="text-xs font-semibold text-emerald-700 uppercase tracking-wide flex items-center gap-2">
                  <CheckCircle className="w-3 h-3" />
                  Output Result
                </h4>
              </div>
              <div className="bg-emerald-50 p-3 rounded-b-md border border-emerald-200">
                <pre className="text-xs overflow-auto text-slate-700 font-mono">
                  <code>{formatResultForDisplay(lastValidResult)}</code>
                </pre>
              </div>
            </div>
          )}
        </div>
      )}
      </div>
    </div>
  );
};
