import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import rehypeHighlight from "rehype-highlight";
import "github-markdown-css"; // GitHub markdown styles
import "highlight.js/styles/github.css"; // GitHub code block theme

import { RenderMessageProps } from "@copilotkit/react-ui";

const TextMessageRender: React.FC<RenderMessageProps> = ({ message }: any) => {
  const { content, role } = message;
  if (!content) return null;

  const isUser = role === "user";

  return (
    <div
      className={`flex w-full ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      <div
        className={`max-w-[70%] px-0 py-0 rounded-xl shadow-sm border text-sm break-words ${
          isUser
            ? "bg-[#f7f7f8] text-gray-900 border-[#d9d9e3]"
            : "bg-white text-gray-800 border-gray-200"
        }`}
      >
        <div className="markdown-body p-5">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw, rehypeHighlight]}
          >
            {content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
};

export default TextMessageRender;
