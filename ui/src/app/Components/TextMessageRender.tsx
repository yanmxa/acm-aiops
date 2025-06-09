import React, { useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import rehypeHighlight from "rehype-highlight";
import "github-markdown-css";
import "highlight.js/styles/github.css";

import { Clipboard, User, Bot } from "lucide-react";
import { RenderMessageProps } from "@copilotkit/react-ui";

const TextMessageRender: React.FC<RenderMessageProps> = ({ message }: any) => {
  const { content, role } = message;
  const markdownRef = useRef<HTMLDivElement>(null);
  if (!content) return null;

  const isUser = role === "user";

  const handleCopy = () => {
    if (markdownRef.current) {
      navigator.clipboard.writeText(content);
    }
  };

  return (
    <div
      className={`flex w-full py-2 items-start ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      {/* User/Assistant Icon */}
      {!isUser && (
        <div className="mr-2 mt-3 text-gray-500">
          <Bot size={20} />
        </div>
      )}

      <div
        className={`relative max-w-[90%] text-sm break-words ${
          isUser
            ? "shadow-sm rounded-xl border border-[#d9d9e3] "
            : "text-gray-800 pb-6 shadow-sm"
        }`}
      >
        <div className="markdown-body p-4 pt-4 pb-4" ref={markdownRef}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw, rehypeHighlight]}
          >
            {content}
          </ReactMarkdown>
        </div>

        {!isUser && (
          <button
            onClick={handleCopy}
            title="Copy"
            className="absolute bottom-2 left-4 text-gray-400 hover:text-gray-700 transition"
          >
            <Clipboard size={16} />
          </button>
        )}
      </div>

      {/* User Icon */}
      {isUser && (
        <div className="ml-2 mt-2 text-gray-500">
          <User size={20} />
        </div>
      )}
    </div>
  );
};

export default TextMessageRender;
