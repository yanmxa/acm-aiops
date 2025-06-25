"use client";

import React, { useState, useEffect } from "react";
import { Spinner } from "./Spinner";
import { CheckCircle } from "lucide-react";

type GenericActionProps = {
  status: "complete" | "executing";
  args: Record<string, unknown>;
  name: string;
  result?: string;
};

export const GenericAction = ({
  status,
  args,
  name,
  result,
}: GenericActionProps) => {
  // State for preserving the last valid result and label
  const [lastValidResult, setLastValidResult] = useState<string | undefined>(result);
  const [lastValidLabel, setLastValidLabel] = useState<string>(name);
  const [isExpanded, setIsExpanded] = useState(true);

  // Helper function to check if a result is valid (not empty)
  const isValidResult = (value: string | undefined): boolean => {
    return Boolean(value && value.trim() !== "");
  };

  // Helper function to format result for display
  const formatResultForDisplay = (rawResult: string | undefined): string => {
    if (!rawResult) return "";
    
    try {
      // Try to parse as JSON object for pretty formatting
      const parsed = JSON.parse(rawResult);
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
    <div className="space-y-2">
      {/* Action Header */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 cursor-pointer hover:text-blue-600 transition-colors text-sm font-bold text-slate-700"
      >
        {/* Status Icon */}
        {isValidResult(lastValidResult) ? (
          <CheckCircle className="w-4 h-4 text-green-600" />
        ) : (
          <Spinner />
        )}
        
        {/* Action Name - Use preserved label */}
        <span className="ml-1">
          {args?.cluster && args.cluster !== "default" ? `${args.cluster}-${lastValidLabel}` : lastValidLabel}
        </span>
        
        {/* Expand/Collapse Indicator */}
        <span className="text-xs text-slate-500">
          {isExpanded ? "▲" : "▼"}
        </span>
      </div>

      {/* Action Details (Collapsible) */}
      {isExpanded && (
        <div className="space-y-2 ml-7 mr-7 rounded-xl bg-gray-100 shadow-sm p-4">
          {/* Input Section */}
          <div>
            <h4 className="text-xs font-semibold text-gray-500 mb-1">Input:</h4>
            <pre className="bg-white p-3 rounded-md text-xs text-left overflow-auto text-gray-800 border border-gray-200">
              <code>{JSON.stringify(args, null, 2)}</code>
            </pre>
          </div>

          {/* Output Section (only show if we have a result) */}
          {isValidResult(lastValidResult) && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 mb-1">Output:</h4>
              <pre className="bg-white p-3 rounded-md text-xs text-left overflow-auto text-gray-800 border border-gray-200">
                <code>{formatResultForDisplay(lastValidResult)}</code>
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
