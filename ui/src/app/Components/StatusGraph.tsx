import React, { useMemo } from "react";
import ReactFlow, {
  Controls,
  Node,
  Edge,
  NodeProps,
  useNodesState,
  useEdgesState,
  ReactFlowProvider,
  Handle,
  Position,
  MarkerType,
} from "react-flow-renderer";
import dagre from "dagre";

const nodeWidth = 180;
const nodeHeight = 70;

interface StatusGraphProps {
  currentStatus?: string;
}

const getLayoutedElements = (
  nodes: Node[],
  edges: Edge[],
  direction: "TB" | "LR" = "TB"
) => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: direction, nodesep: 50, ranksep: 80 });

  nodes.forEach((node) =>
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight })
  );
  edges.forEach((edge) =>
    dagreGraph.setEdge(edge.source, edge.target)
  );

  dagre.layout(dagreGraph);

  const layoutedNodes = nodes.map((node) => {
    const { x, y } = dagreGraph.node(node.id);
    return {
      ...node,
      position: { x: x - nodeWidth / 2, y: y - nodeHeight / 2 },
      targetPosition: direction === "TB" ? Position.Top : Position.Left,
      sourcePosition: direction === "TB" ? Position.Bottom : Position.Right,
    };
  });

  return { nodes: layoutedNodes, edges };
};

const StatusNode = ({ data }: NodeProps) => {
  const { label, status, message, icon } = data;

  const baseClasses = "px-4 py-3 rounded-xl text-sm font-medium shadow-md border transition-all duration-300 text-center min-w-[160px]";
  
  const statusStyles: Record<string, string> = {
    completed: "bg-green-50 text-green-700 border-green-200 shadow-green-100 scale-110",
    processing: "bg-blue-50 text-blue-700 border-blue-200 shadow-blue-100 scale-110 animate-pulse",
    pending: "bg-gray-50 text-gray-500 border-gray-200 shadow-gray-100",
    error: "bg-red-50 text-red-700 border-red-200 shadow-red-100",
  };

  const iconSize = status === "processing" || status === "completed" ? "text-lg" : "text-base";

  return (
    <div className="flex flex-col items-center space-y-2">
      <div className={`${baseClasses} ${statusStyles[status] || statusStyles.pending}`}>
        <div className="flex items-center justify-center space-x-2">
          <span className={iconSize}>{icon}</span>
          <span>{label}</span>
        </div>
      </div>
      {message && (
        <div className={`text-xs px-2 py-1 rounded bg-white shadow-sm border max-w-[180px] text-center ${
          status === "processing" ? "animate-pulse text-blue-600 border-blue-200" : "text-gray-600 border-gray-200"
        }`}>
          {message}
        </div>
      )}
      <Handle type="target" position={Position.Top} style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0 }} />
    </div>
  );
};

const nodeTypes = {
  statusNode: StatusNode,
};

const getWorkflowNodes = (currentStatus?: string): Node[] => {
  const getNodeStatus = (nodeKey: string) => {
    if (!currentStatus || currentStatus === "idle") return "pending";
    
    const status = currentStatus.toLowerCase();
    
    // Determine node status based on current workflow state
    if (status.includes("router")) {
      if (nodeKey === "router") return status.includes("completed") ? "completed" : "processing";
      return "pending";
    }
    
    if (status.includes("tool")) {
      if (nodeKey === "router") return "completed";
      if (nodeKey === "tools") return status.includes("completed") ? "completed" : "processing";
      return "pending";
    }
    
    if (status.includes("analyzer") || status.includes("data")) {
      if (nodeKey === "router") return "completed";
      if (nodeKey === "tools") return "completed";
      if (nodeKey === "analyzer") return status.includes("completed") ? "completed" : "processing";
      return "pending";
    }
    
    if (status.includes("response")) {
      if (nodeKey === "router") return "completed";
      if (nodeKey === "tools") return "completed";
      if (nodeKey === "analyzer") return "completed";
      if (nodeKey === "response") return status.includes("completed") ? "completed" : "processing";
      return "pending";
    }
    
    return "pending";
  };

  const getNodeMessage = (nodeKey: string, status: string) => {
    if (status !== "processing") return "";
    
    const messages = {
      router: "Analyzing request...",
      tools: "Executing tools...",
      analyzer: "Processing data...",
      response: "Generating response...",
    };
    
    return messages[nodeKey as keyof typeof messages] || "";
  };

  return [
    {
      id: "router",
      type: "statusNode",
      data: { 
        label: "Router", 
        status: getNodeStatus("router"),
        message: getNodeMessage("router", getNodeStatus("router")),
        icon: "🎯"
      },
      position: { x: 0, y: 0 },
    },
    {
      id: "tools",
      type: "statusNode",
      data: { 
        label: "Tool Executor", 
        status: getNodeStatus("tools"),
        message: getNodeMessage("tools", getNodeStatus("tools")),
        icon: "⚙️"
      },
      position: { x: 0, y: 0 },
    },
    {
      id: "analyzer",
      type: "statusNode",
      data: { 
        label: "Data Analyzer", 
        status: getNodeStatus("analyzer"),
        message: getNodeMessage("analyzer", getNodeStatus("analyzer")),
        icon: "📊"
      },
      position: { x: 0, y: 0 },
    },
    {
      id: "response",
      type: "statusNode",
      data: { 
        label: "Response Generator", 
        status: getNodeStatus("response"),
        message: getNodeMessage("response", getNodeStatus("response")),
        icon: "💬"
      },
      position: { x: 0, y: 0 },
    },
  ];
};

const getWorkflowEdges = (nodes: Node[]): Edge[] => {
  return nodes.slice(0, -1).map((node, index) => {
    const nextNode = nodes[index + 1];
    return {
      id: `e${node.id}-${nextNode.id}`,
      source: node.id,
      target: nextNode.id,
      animated: node.data.status === "completed",
      style: { 
        stroke: node.data.status === "completed" ? "#10b981" : "#cbd5e1",
        strokeWidth: node.data.status === "completed" ? 2 : 1
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: node.data.status === "completed" ? "#10b981" : "#94a3b8",
      },
      type: "smoothstep",
    };
  });
};

export default function StatusGraph({ currentStatus }: StatusGraphProps) {
  const workflowNodes = useMemo(() => getWorkflowNodes(currentStatus), [currentStatus]);
  const workflowEdges = useMemo(() => getWorkflowEdges(workflowNodes), [workflowNodes]);

  const { nodes: layoutedNodes, edges: layoutedEdges } = useMemo(
    () => getLayoutedElements(workflowNodes, workflowEdges, "TB"),
    [workflowNodes, workflowEdges]
  );

  const [nodes, , onNodesChange] = useNodesState(layoutedNodes);
  const [edges, , onEdgesChange] = useEdgesState(layoutedEdges);

  return (
    <ReactFlowProvider>
      <div className="w-full h-[400px] mx-auto border border-gray-100 rounded-xl shadow-sm bg-gradient-to-br from-white to-gray-50">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          nodesDraggable={false}
          zoomOnScroll={false}
          panOnScroll={false}
          panOnDrag={false}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitViewOptions={{ padding: 0.2 }}
        >
          <Controls showZoom={false} showFitView={false} showInteractive={false} />
        </ReactFlow>
      </div>
    </ReactFlowProvider>
  );
}
