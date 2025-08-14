"use client";
import React, { useCallback } from "react";
import "@copilotkit/react-ui/styles.css";
import "./Chat.module.css";
import { useCopilotChat, useCoAgent, useCopilotAction, useCoAgentStateRender } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { State, RechartParameters } from '../lib/agent_state';
import TextMessageRender from "./TextMessageRender";
import { GenericAction } from "./GenericAction";
import { RechartCollection } from "./ChartOutput";
import ProgressBar from "./Progress";
import { useLangGraphInterrupt } from "@copilotkit/react-core";

export default function Chat() {
  const { state } = useCoAgent<State>({
    name: "chat_agent",
  });

  // Register action handlers
  const actionNames = ["kubectl", "prom_query", "prom_range", "prom_discover", "prom_metadata", "prom_targets"];
  actionNames.forEach((actionName) => {
    useCopilotAction({
      name: actionName,
      available: "disabled",
      render: (obj: any) => {
        const { status, args, name, result } = obj;
        const finalResult = result;
        const displayStatus = status === "inProgress" ? "executing" : status;
        return <GenericAction status={displayStatus} args={args} name={actionName} result={finalResult} />;
      },
    });
  });

  useCopilotAction({
    name: "render_recharts",
    available: "disabled",
    parameters: RechartParameters as any[],
    render: (obj: any) => {
      const charts = obj?.args?.data?.charts ?? [];
      return <RechartCollection charts={charts} />;
    },
  });

  useCoAgentStateRender<State>({
    name: "chat_agent",
    render: ({ status, state, nodeName }) => {
      const progress = state?.progress;
      console.log("update message", status, state, nodeName, "progress:", progress);
      return (
        <ProgressBar 
          label="Processing" 
          status={status} 
          progress={progress}
        />
      )
    },
  });

  // // styles omitted for brevity
  // useLangGraphInterrupt({
  //   render: ({ event, resolve }) => {
  //     console.log("event", event);
  //     const { name, args } = event.value;
  //     console.log("name", name, "args", args);
  //     return (
  //       <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 my-2">
  //         <div className="flex items-center justify-between mb-2">
  //           <div className="flex items-center space-x-2">
  //             <span className="text-blue-600">🔐</span>
  //             <span className="text-sm font-medium text-blue-800">
  //               Approve {name}?
  //             </span>
  //           </div>
  //           <div className="flex space-x-2">
  //             <button
  //               onClick={() => resolve("approved")}
  //               className="px-3 py-1 bg-green-500 text-white text-sm rounded hover:bg-green-600"
  //             >
  //               ✓ Yes
  //             </button>
  //             <button
  //               onClick={() => resolve("denied")}
  //               className="px-3 py-1 bg-red-500 text-white text-sm rounded hover:bg-red-600"
  //             >
  //               ✗ No
  //             </button>
  //           </div>
  //         </div>
  //         {args && Object.keys(args).length > 0 && (
  //           <div className="bg-white rounded border p-2 mt-2">
  //             <div className="text-xs text-gray-600 mb-1">Parameters:</div>
  //             <pre className="text-xs text-gray-800 whitespace-pre-wrap overflow-x-auto">
  //               {JSON.stringify(args, null, 2)}
  //             </pre>
  //           </div>
  //         )}
  //       </div>
  //     );
  //   }
  // });

  const { visibleMessages } = useCopilotChat();
  
  return (
    <div className="flex justify-center items-start h-screen w-screen pt-[1%]">
      {/* Welcome message */}
      {visibleMessages.length === 0 && (
        <div className="absolute top-[35%] left-0 right-0 mx-auto w-full max-w-3xl z-40 pl-10">
          <h1 className="text-4xl font-bold text-gray-800 mb-3">Hello, I am an AIOps agent!</h1>
          <p className="text-2xl text-gray-600">I can assist you with multiple Kubernetes clusters</p>
        </div>
      )}

      <div className="w-7/10 h-8/10 bg-gray-50">
        <CopilotChat 
          className="h-full rounded-lg bg-gray-50"
          RenderTextMessage={TextMessageRender}
        />
      </div>
    </div>
  );
};

