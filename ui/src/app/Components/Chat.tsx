
"use client";
import React, { useState, useEffect } from "react";
import "@copilotkit/react-ui/styles.css";
import { CopilotKit, useCopilotChat, useLangGraphInterrupt,useCoAgentStateRender } from "@copilotkit/react-core";
import { CopilotChat, useCopilotChatSuggestions } from "@copilotkit/react-ui";
import { Approve } from "./Approve";
import { Actions } from './Action';
import "./Chat.module.css";
import Chart from "./ChartOutput";
import ProgressBar  from "./Progress";
import { AgentState } from "../lib/agent_state";
import TextMessageRender from "./TextMessageRender";
import ChartOutput from "./ChartOutput";

export function CustomRenderAgentStateMessage(props: any) {
  const agentState: AgentState = props.message.state
  const { actions, progress } = agentState
  if (!actions) {
    return null
  }
  return <Actions actions={actions} />
}


export default function Chat() {
  useLangGraphInterrupt({
      enabled: ({ eventValue }) => eventValue.type === 'approval',
      render: ({ event, resolve }) => {
      const handleAnswer = (answer: boolean) => {
        resolve(answer.toString());  // or just return resolve(answer);
      };
      return (
        <Approve
          content={event.value.content}
          onAnswer={handleAnswer}
        />
      );
    },
  });


  useCoAgentStateRender<AgentState>({
    name: "chat_agent",
    render: ({ status, state }) => {
      const { actions, progress } = state
      return (
        <>
          {status === "inProgress" && progress && <ProgressBar progress={progress.value} label={progress.label} />}
          {actions && <Actions actions={actions} />}
        </>
      );
    },
  });

  // useCopilotChatSuggestions({
  //   instructions: `Provide some suggested actions to perform like "Go to mars". Make sure to always have a "Go to mars" action in suggestions and strictly show it as the first action.`,
  // })
  const {
    visibleMessages, // An array of messages that are currently visible in the chat.
    appendMessage, // A function to append a message to the chat.
    setMessages, // A function to set the messages in the chat.
    deleteMessage, // A function to delete a message from the chat.
    reloadMessages, // A function to reload the messages from the API.
    stopGeneration, // A function to stop the generation of the next message.
    reset, // A function to reset the chat.
    isLoading, // A boolean indicating if the chat is loading.
  }= useCopilotChat();

  // For dev purposes. Will be removed in production.
  console.log("visibleMessages", visibleMessages)
  // console.log("action")
  // console.log("agent state", agentState)

  const rechart_data = {
        "data": [
            {"name": "2025-06-05T00:00:00", "multiclusterhub-operator-b5df4469-wgqs5": 229.23046875, "multiclusterhub-operator-b5df4469-9j87m": 29.22265625},
            {"name": "2025-06-05T05:00:00", "multiclusterhub-operator-b5df4469-wgqs5": 214.38671875, "multiclusterhub-operator-b5df4469-9j87m": 35.41015625},
            {"name": "2025-06-05T10:00:00", "multiclusterhub-operator-b5df4469-wgqs5": 251.0234375, "multiclusterhub-operator-b5df4469-9j87m": 35.421875},
            {"name": "2025-06-05T15:00:00", "multiclusterhub-operator-b5df4469-wgqs5": 195.06640625, "multiclusterhub-operator-b5df4469-9j87m": 34.34765625},
            {"name": "2025-06-05T20:00:00", "multiclusterhub-operator-b5df4469-wgqs5": 248.08203125, "multiclusterhub-operator-b5df4469-9j87m": 35.5},
            {"name": "2025-06-06T01:00:00", "multiclusterhub-operator-b5df4469-wgqs5": 198.421875, "multiclusterhub-operator-b5df4469-9j87m": 36.51171875},
            {"name": "2025-06-06T06:00:00", "multiclusterhub-operator-b5df4469-wgqs5": 217.703125, "multiclusterhub-operator-b5df4469-9j87m": 35.9921875},
            {"name": "2025-06-06T11:00:00", "multiclusterhub-operator-b5df4469-wgqs5": 290.55859375, "multiclusterhub-operator-b5df4469-9j87m": 36.8203125},
            {"name": "2025-06-06T16:00:00", "multiclusterhub-operator-b5df4469-wgqs5": 254.40625, "multiclusterhub-operator-b5df4469-9j87m": 37.07421875},
            {"name": "2025-06-06T21:00:00", "multiclusterhub-operator-b5df4469-wgqs5": 252.05078125, "multiclusterhub-operator-b5df4469-9j87m": 35.84375}
        ],
        "type": "range",
        "unit": "MiB"
    }

  return (
    <div className="flex justify-center items-start h-screen w-screen border border-white pt-[1%]">

      {/* Welcome message that disappears when there are messages */}
      {visibleMessages.length === 0 && (
          <div className="absolute top-[35%] left-0 right-0 mx-auto w-full max-w-3xl z-40 pl-10">
              <h1 className="text-4xl font-bold text-black mb-3">Hello, I am an ACM agent!</h1>
              <p className="text-2xl text-gray-500">I can assistant you with the multiple Kubernetes clusters</p>
          </div>
      )}

      {/* <ChartOutput output={rechart_data} /> */}

      <div className="w-7/10 h-8/10 bg-gray-50 border border-white">
        <CopilotChat className="h-full rounded-lg"
          // RenderAgentStateMessage={CustomRenderAgentStateMessage}
          RenderTextMessage={TextMessageRender}
        />
      </div>
    </div>
  );
};