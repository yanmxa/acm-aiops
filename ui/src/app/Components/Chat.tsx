
"use client";
import React, { useState, useEffect } from "react";
import "@copilotkit/react-ui/styles.css";
import { CopilotKit, useCopilotChat, useLangGraphInterrupt,useCoAgentStateRender, useCopilotAction } from "@copilotkit/react-core";
import { CopilotChat, useCopilotChatSuggestions } from "@copilotkit/react-ui";
import { Approve } from "./Approve";
import { Actions } from './Action';
import "./Chat.module.css";
import Chart from "./ChartOutput";
import ProgressBar  from "./Progress";
import { AgentState, RechartParameters } from '../lib/agent_state';
import TextMessageRender from "./TextMessageRender";
import ChartOutput from "./ChartOutput";
import { GenericAction } from "./GenericAction";
import { RechartCollection } from "./ChartOutput";

export default function Chat() {
  // useLangGraphInterrupt({
  //     enabled: ({ eventValue }) => eventValue.type === 'approval',
  //     render: ({ event, resolve }) => {
  //     const handleAnswer = (answer: boolean) => {
  //       resolve(answer.toString());  // or just return resolve(answer);
  //     };
  //     return (
  //       <Approve
  //         content={event.value.content}
  //         onAnswer={handleAnswer}
  //       />
  //     );
  //   },
  // });

  // tool
  // useCopilotAction
  const actionNames = ["kubectl", "clusters", "connect_cluster", "prometheus"];

  actionNames.forEach((actionName) => {
    useCopilotAction({
      name: actionName,
      available: "disabled", // Don't allow the agent or UI to call this tool as its only for rendering
      render: (obj) => {
        const { status, args, name, result } = obj as any;
        console.log("actionName", actionName, status, args, name, result);
        return (
          <GenericAction status={status} args={args} name={name} result={result} />
        );
      },
    });
  });

  useCopilotAction({
      name: "render_recharts",
      available: "disabled", // Don't allow the agent or UI to call this tool as its only for rendering
      parameters: RechartParameters as any[],
      render: (obj: any) => {
        const { status, args, name, result } = obj as any;
        const charts = obj?.args?.data?.charts ?? [];
        return <RechartCollection charts={charts} />
      },
  });

  // for the agent state
  useCoAgentStateRender<AgentState>({
    name: "chat_agent",
    render: (agentState: any) => {
      console.log("agentState", agentState);
      return (
        <>
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
          RenderTextMessage={TextMessageRender}
        />
      </div>
    </div>
  );
};

