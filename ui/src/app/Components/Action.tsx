"use client";

import React, { useState } from "react";
import { Spinner } from "./Spinner";
import { AgentState, ActionState } from "../lib/agent_state";
import { RenderMessageProps } from "@copilotkit/react-ui";
import { Clipboard, User, Bot, Wrench } from "lucide-react";
import ChartOutput from "./ChartOutput";

// Note: no result can get from the render message
export function CustomRenderActionExecutionMessage(props: RenderMessageProps) {

  const [expanded, setExpanded] = useState(true);

  const baseClass = props.inProgress
    ? "text-xl font-bold text-slate-700"
    : "text-sm font-bold text-slate-700";

  const actionMessage: any = props.message

  const parsedArgs = (() => {
    try {
      return typeof actionMessage.arguments === "object"
        ? JSON.stringify(actionMessage.arguments, null, 2)
        : JSON.stringify(JSON.parse(actionMessage.arguments), null, 2);
    } catch {
      return String(actionMessage.arguments);
    }
  })();

  let output = ""
  if (props.actionResult) {
    output = (() => {
    try {
      return typeof props.actionResult === "object"
        ? JSON.stringify(props.actionResult, null, 2)
        : JSON.stringify(JSON.parse(props.actionResult), null, 2);
    } catch {
      return String(props.actionResult);
    }
  })();
  }

  return (
    <div className="space-y-2">
      <div
        onClick={() => setExpanded((prev) => !prev)}
        className={`flex items-center gap-2 cursor-pointer hover:text-blue-600 transition-colors ${baseClass}`}
      >
        {props.inProgress ?  
        (
          <Spinner />
        ) : (
          <span className="text-green-600">✓</span>
        )}

        <span>{String(actionMessage.name)}</span>
        <span className="ml-auto text-xs text-slate-500">{expanded ? "▲" : "▼"}</span>
      </div>

      {expanded && (
        <div className="space-y-2">
          <div>
            <h4 className="text-xs font-semibold text-gray-500 mb-1">Input:</h4>
            <pre className="bg-white p-3 rounded-md text-xs text-left overflow-auto text-gray-800 border border-gray-200">
              <code>{parsedArgs}</code>
            </pre>
          </div>

          {!props.inProgress && output && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 mb-1">Output:</h4>
              <pre className="bg-white p-3 rounded-md text-xs text-left overflow-auto text-gray-800 border border-gray-200">
                <code>{output}</code>
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}


export const Actions = ({ actions }: { actions: ActionState[] }) => {
  if (!actions || actions.length === 0) {
        return null;
  }

  const firstPendingIndex = actions.findIndex((s) => s.status === "pending");

  return (
    <div className="flex py-2">
      <div className="mr-2 mt-3 text-gray-500">
          <Wrench size={20} />
      </div>
      <div className="bg-gray-100 rounded-lg w-[90%] p-4 text-black space-y-4">
        {actions.map((action, index) => (
          <Action
            key={index}
            action={action}
            isFirstPending={index === firstPendingIndex && action.status === "pending"}
          />
        ))}
      </div>
    </div>
  );
};

export const Action = ({
  action,
  isFirstPending,
}: {
  action: ActionState;
  isFirstPending?: boolean;
}) => {
  const [expanded, setExpanded] = useState(true);

  const baseClass = isFirstPending
    ? "text-xl font-bold text-slate-700"
    : "text-sm font-bold text-slate-700";

  const parsedArgs = (() => {
    try {
      return typeof action.args === "object"
        ? JSON.stringify(action.args, null, 2)
        : JSON.stringify(JSON.parse(action.args), null, 2);
    } catch {
      return String(action.args);
    }
  })();

  const parsedOutput = (() => {
    try {
      return typeof action.output === "object"
        ? JSON.stringify(action.output, null, 2)
        : JSON.stringify(JSON.parse(action.output), null, 2);
    } catch {
      return String(action.output);
    }
  })();

  let chartOutput: any = null;

  if (action.name === "prometheus") {
    try {
      chartOutput =
        typeof action.output === "object"
          ? action.output
          : JSON.parse(action.output);
    } catch {
      chartOutput = null;
    }
    console.log("chart output: ", action.output)
    console.log("chart output object: ", chartOutput)
  }

  return (
    <div className="space-y-2">
      <div
        onClick={() => setExpanded((prev) => !prev)}
        className={`flex items-center gap-2 cursor-pointer hover:text-blue-600 transition-colors ${baseClass}`}
      >
        {action.status === "completed" ? (
          <span className="text-green-600">✓</span>
        ) : (
          <Spinner />
        )}
        <span>{String(action.name)}</span>
        <span className="ml-auto text-xs text-slate-500">{expanded ? "▲" : "▼"}</span>
      </div>

      {expanded && (
        <div className="space-y-2">
          <div>
            <h4 className="text-xs font-semibold text-gray-500 mb-1">Input:</h4>
            <pre className="bg-white p-3 rounded-md text-xs text-left overflow-auto text-gray-800 border border-gray-200">
              <code>{parsedArgs}</code>
            </pre>
          </div>

          {action.status === "completed" && action.output && (
            <div>
              <h4 className="text-xs font-semibold text-gray-500 mb-1">Output:</h4>
              <pre className="bg-white p-3 rounded-md text-xs text-left overflow-auto text-gray-800 border border-gray-200">
                <code>{parsedOutput}</code>
              </pre>
            </div>
          )}
        </div>
      )}
      {/* ✅ Render chart only for prometheus */}
      {/* {action.name === "prometheus"  && chartOutput && (<ChartOutput output={chartOutput} />)} */}
    </div>
  );
};