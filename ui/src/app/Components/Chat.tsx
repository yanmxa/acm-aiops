"use client";
import React, { useCallback } from "react";
import "@copilotkit/react-ui/styles.css";
import { useCopilotChat, useCoAgent, useCopilotAction, useCoAgentStateRender } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import { AgentState, RechartParameters } from '../lib/agent_state';
import TextMessageRender from "./TextMessageRender";
import { GenericAction } from "./GenericAction";
import { RechartCollection } from "./ChartOutput";
import ProgressBar from "./Progress";

export default function Chat() {
  const { state } = useCoAgent<AgentState>({
    name: "chat_agent",
    initialState: {
      patch_action_result: {},
    },
  });

  // Register action handlers
  const actionNames = ["kubectl", "clusters", "connect_cluster", "prometheus"];
  actionNames.forEach((actionName) => {
    useCopilotAction({
      name: actionName,
      available: "disabled",
      render: (obj: any) => {
        const { status, args, name, result } = obj;
        const finalResult = getActionResult(result, state, actionName, args);
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

  // useCoAgentStateRender<AgentState>({
  //   name: "chat_agent",
  //   render: ({ status, state, nodeName }) => {
  //     const update = state?.update;
  //     console.log(status, state, nodeName)
  //     return (
  //       <ProgressBar label={update} status={status} />
  //     )
  //   },
  // });

  const { visibleMessages } = useCopilotChat();
  
  return (
    <div className="flex justify-center items-start h-screen w-screen border border-white pt-[1%]">
      {/* Welcome message */}
      {visibleMessages.length === 0 && (
        <div className="absolute top-[35%] left-0 right-0 mx-auto w-full max-w-3xl z-40 pl-10">
          <h1 className="text-4xl font-bold text-black mb-3">Hello, I am an ACM agent!</h1>
          <p className="text-2xl text-gray-500">I can assist you with multiple Kubernetes clusters</p>
        </div>
      )}

      <div className="w-7/10 h-8/10 bg-gray-50 border border-white">
        <CopilotChat 
          className="h-full rounded-lg"
          RenderTextMessage={TextMessageRender}
        />
      </div>
    </div>
  );
};
  // Helper function to get action result with fallback logic
  const getActionResult = (result: any, state: any, actionName: string, args?: any) => {
    if (result) return result;
    
    const patchActionResult = (state as any)?.patch_action_result || {};
    console.log("patchActionResult", patchActionResult)
    
    // Try cluster-specific key first
    if (args?.cluster && args.cluster !== "default") {
      const clusterKey = `${actionName}-${args.cluster}`;
      if (patchActionResult[clusterKey]) return patchActionResult[clusterKey];
    }
    
    // Fallback to simple action name
    return patchActionResult[actionName];
  };

