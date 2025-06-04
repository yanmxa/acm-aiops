"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useCoAgent } from "@copilotkit/react-core";
import { AgentState } from "../lib/agent_state";

export default function Toggle() {
  const [open, setOpen] = useState(false);
  const [kubeconfig, setKubeconfig] = useState("");
  const [submittedKubeconfig, setSubmittedKubeconfig] = useState("");

  const panelWidth = 320;
  const collapsedWidth = 28;

  // const {
  //   state: agentState,
  //   setState,
  //   run,
  // } = useCoAgent<AgentState>({
  //   name: "chat_agent",
  //   initialState: {
  //     hubKubeconfig: ""
  //   }
  // })
  const {
        state: agentState,
        setState,
        nodeName
    } = useCoAgent<AgentState>({
      name: "chat_agent",
    })

    // setup to be called when some event in the app occurs
  const submitHubKubeconfig = () => {
    if (submittedKubeconfig != kubeconfig) {
      setSubmittedKubeconfig(kubeconfig)
      agentState.hubKubeconfig = kubeconfig
      setState(agentState)
      console.log("setting agent hub kubeconfig", agentState.hubKubeconfig)
    }
    setKubeconfig(""); // Clear textarea
  };
  console.log("submittedKubeconfig", submittedKubeconfig)

  return (
    <div
      className="fixed top-24 right-0 z-50 h-64 flex shadow-lg transition-all duration-300 ease-in-out overflow-hidden rounded-l-xl"
      style={{
        width: open ? panelWidth : collapsedWidth,
        backgroundColor: open ? "#f8f9fa" : "#e2e8f0", // light gray or muted blue-gray
      }}
    >
      {/* Clickable Left Strip (acts like a toggle bar) */}
      <div
        className="w-7 flex items-center justify-center cursor-pointer hover:bg-gray-300 transition-colors"
        onClick={() => setOpen((prev) => !prev)}
        title={open ? "Hide panel" : "Show panel"}
      >
        <div className="h-10 w-6 text-gray-600 flex items-center justify-center">
          {open ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
        </div>
      </div>

      {/* Panel Content */}
      {open && (
        <div className="p-4 w-[288px] flex flex-col justify-between text-sm">
          <div>
            <h2 className="text-base font-semibold mb-2 text-gray-800">
              Submit Kubeconfig
            </h2>
            <textarea
              placeholder="Paste kubeconfig here"
              value={kubeconfig}
              onChange={(e) => setKubeconfig(e.target.value)}
              className="w-full h-24 border border-gray-300 rounded p-2 text-sm resize-none bg-white"
            />
          </div>
          <div>
            <button
              className="mt-3 bg-red-600 text-white py-1.5 px-4 rounded-md hover:bg-red-700 transition"
              onClick={() => submitHubKubeconfig()}
            >
              Commit
            </button>
            {submittedKubeconfig && (
              <div className="mt-3 border-t pt-2 text-xs text-gray-600 whitespace-pre-wrap">
                <strong>Submitted:</strong>
                <pre className="mt-1">{submittedKubeconfig}</pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
