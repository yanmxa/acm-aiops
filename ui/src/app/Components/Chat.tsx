
"use client";
import React, { useState, useEffect } from "react";
import "@copilotkit/react-ui/styles.css";
import { CopilotKit, useCopilotChat, useLangGraphInterrupt,useCoAgentStateRender } from "@copilotkit/react-core";
import { CopilotChat, useCopilotChatSuggestions } from "@copilotkit/react-ui";
import { useCoAgent } from "@copilotkit/react-core";
import { Approve } from "./Approve";
import { Spinner } from "./Spinner";
import { AgentState } from "../lib/agent_state";
import { Actions } from './Action';
import "./Chat.module.css";

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
    render: ({ state }) => {
      if (!state.actions || state.actions.length === 0) {
        return null;
      }
      return (
        <Actions actions={state["actions"]} />
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
    <div className="flex justify-center items-center h-screen w-screen">

      {/* Welcome message that disappears when there are messages */}
      {visibleMessages.length === 0 && (
          <div className="absolute top-[25%] left-0 right-0 mx-auto w-full max-w-3xl z-40 pl-10">
              <h1 className="text-4xl font-bold text-black mb-3">Hello, I am an ACM agent!</h1>
              <p className="text-2xl text-gray-500">I can assistant you with the multiple Kubernetes clusters</p>
          </div>
      )}
      
      <div className="w-7/10 h-7/10">
        <CopilotChat
          className="h-full rounded-lg"
          // labels={{
          //   // initial: "I'm an Agent for Advanced Cluster Management. Try saying 'list clusters!'"
          // }} 
        />
      </div>
    </div>
  );
};