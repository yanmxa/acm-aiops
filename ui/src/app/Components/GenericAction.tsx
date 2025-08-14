"use client";

import React, { useState, useEffect } from "react";
import { Spinner } from "./Spinner";
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
  status,
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
    <div className="mb-3">
      {/* Action Header */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="bg-white border border-gray-200 shadow-sm rounded-lg p-3 cursor-pointer hover:shadow-md hover:border-gray-300 transition-all duration-200 group flex items-center gap-3"
      >
        {/* Tool Icon */}
        <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-slate-50 to-slate-100 group-hover:from-slate-100 group-hover:to-slate-200 rounded-xl flex items-center justify-center transition-all duration-200 text-slate-600 group-hover:text-slate-700">
          {getToolIcon()}
        </div>

        {/* Action Name */}
        <div className="flex-1 min-w-0">
          <div className="text-sm font-semibold text-slate-800 group-hover:text-blue-700 transition-colors">
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

        {/* Status Icon */}
        <div className="flex-shrink-0">
          {isValidResult(lastValidResult) ? (
            <div className="w-7 h-7 bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-full flex items-center justify-center shadow-sm">
              <CheckCircle className="w-4 h-4 text-emerald-600" />
            </div>
          ) : (
            <div className="w-7 h-7 bg-gradient-to-br from-blue-50 to-blue-100 rounded-full flex items-center justify-center shadow-sm">
              <div className="w-4 h-4">
                <Spinner />
              </div>
            </div>
          )}
        </div>
        
        {/* Expand/Collapse Indicator */}
        <div className="flex-shrink-0 w-6 h-6 bg-slate-100 group-hover:bg-slate-200 rounded-md flex items-center justify-center transition-colors">
          <span className="text-xs text-slate-500 group-hover:text-slate-700 transition-colors">
            {isExpanded ? "▲" : "▼"}
          </span>
        </div>
      </div>

      {/* Action Details (Collapsible) */}
      {isExpanded && (
        <div className="mt-3">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            {/* Input Section */}
            <div className="border-b border-gray-100">
              <div className="bg-gradient-to-r from-slate-50 to-slate-100 px-4 py-2.5">
                <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wide flex items-center gap-2">
                  <Hammer className="w-3 h-3" />
                  Input Parameters
                </h4>
              </div>
              <div className="p-3">
                <pre className="bg-slate-50 p-3 rounded-md text-xs overflow-auto text-slate-700 border border-slate-200 font-mono">
                  <code>{JSON.stringify(args, null, 2)}</code>
                </pre>
              </div>
            </div>

            {/* Output Section (only show if we have a result) */}
            {isValidResult(lastValidResult) && (
              <div>
                <div className="bg-gradient-to-r from-emerald-50 to-emerald-100 px-4 py-2.5">
                  <h4 className="text-xs font-semibold text-emerald-700 uppercase tracking-wide flex items-center gap-2">
                    <CheckCircle className="w-3 h-3" />
                    Output Result
                  </h4>
                </div>
                <div className="p-3">
                  <pre className="bg-emerald-50 p-3 rounded-md text-xs overflow-auto text-slate-700 border border-emerald-200 font-mono">
                    <code>{formatResultForDisplay(lastValidResult)}</code>
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
