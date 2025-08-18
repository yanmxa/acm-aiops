import React, { useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import rehypeHighlight from "rehype-highlight";
import "github-markdown-css";
import "highlight.js/styles/github.css";

import { Clipboard, User } from "lucide-react";
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

  if (isUser) {
    // User messages - special bubble style
    return (
      <div className="w-full py-4 px-6">
        <div className="group flex items-start gap-4 justify-end">
          {/* User Message Content */}
          <div className="flex-1 max-w-[85%] text-right">
            {/* Role Label */}
            <div className="text-xs font-medium text-gray-500 mb-2 text-right">
              You
            </div>

            {/* Message Bubble */}
            <div className="relative inline-block max-w-full text-sm bg-blue-500 text-white rounded-2xl rounded-br-md px-4 py-3">
              <div className="markdown-body" ref={markdownRef} style={{
                background: 'transparent',
                color: 'white',
                textAlign: 'left'
              }}>
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeRaw, rehypeHighlight]}
                  components={{
                    p: ({ children }) => (
                      <p className="text-white mb-2 last:mb-0">
                        {children}
                      </p>
                    ),
                    code: ({ children, className }) => (
                      <code className={`${className} bg-blue-600 bg-opacity-50 text-white px-1 py-0.5 rounded`}>
                        {children}
                      </code>
                    ),
                    pre: ({ children }) => (
                      <pre className="bg-blue-600 bg-opacity-30 text-white border-blue-400 p-3 rounded-lg border overflow-x-auto">
                        {children}
                      </pre>
                    ),
                  }}
                >
                  {content}
                </ReactMarkdown>
              </div>
            </div>
          </div>

          {/* User Avatar */}
          <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center bg-blue-500 text-white">
            <User size={20} />
          </div>
        </div>
      </div>
    );
  }

  // Assistant messages - clean panel without header
  return (
    <div className="w-full py-2 px-6">
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
        {/* Assistant Content */}
        <div className="markdown-body" ref={markdownRef}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeRaw, rehypeHighlight]}
          >
            {content}
          </ReactMarkdown>
        </div>

        {/* Copy Button */}
        <button
          onClick={handleCopy}
          title="Copy message"
          className="mt-3 text-gray-400 hover:text-gray-700 transition-colors duration-200 flex items-center gap-2 text-sm"
        >
          <Clipboard size={16} />
          <span>Copy</span>
        </button>
      </div>
    </div>
  );
};

export default TextMessageRender;
