"use client";

import React, { useState } from "react";
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
  console.log(name, status, args, result)

  const parsedArgs = JSON.stringify(args, null, 2);

   const parsedResult =
    result && typeof result === "object" && result !== null
      ? JSON.stringify(result, null, 2)
      : String(result);


  const displayName =
    args?.cluster && args.cluster != "default" ? `${args.cluster}- ${name}` : name;

  const [expanded, setExpanded] = useState(true);

  return (
    <div className="space-y-2">
      <div
        onClick={() => setExpanded((prev) => !prev)}
        className="flex items-center gap-2 cursor-pointer hover:text-blue-600 transition-colors text-sm font-bold text-slate-700"
      >
        {result ? (
          <CheckCircle className="w-4 h-4 text-green-600" />
        ) : (
          <Spinner />
        )}
        <span className="ml-1">{displayName}</span>
        <span className="text-xs text-slate-500">{expanded ? "▲" : "▼"}</span>
      </div>

      {expanded && (
        <div className="space-y-2 ml-7 mr-7 rounded-xl bg-gray-100 shadow-sm p-4">
          <div>
            <h4 className="text-xs font-semibold text-gray-500 mb-1">Input:</h4>
            <pre className="bg-white p-3 rounded-md text-xs text-left overflow-auto text-gray-800 border border-gray-200">
              <code>{parsedArgs}</code>
            </pre>
          </div>

          {result && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 mb-1">Output:</h4>
              <pre className="bg-white p-3 rounded-md text-xs text-left overflow-auto text-gray-800 border border-gray-200">
                <code>{parsedResult}</code>
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
