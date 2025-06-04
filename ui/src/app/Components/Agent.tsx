"use client";
import React, { useState, useEffect } from "react";
import "@copilotkit/react-ui/styles.css";
import { CopilotKit, useCopilotChat, useLangGraphInterrupt } from "@copilotkit/react-core";
import { CopilotChat, useCopilotChatSuggestions } from "@copilotkit/react-ui";
import Toggle from "./Toggle";
import Chat from "./Chat";

const ChatAgent: React.FC = () => {
  return (
    <CopilotKit
      runtimeUrl="api/copilotkit"
      showDevConsole={true}
      agent="chat_agent"
    >
      <Toggle />
      <Chat />
    </CopilotKit>
  );
};

export default ChatAgent;
