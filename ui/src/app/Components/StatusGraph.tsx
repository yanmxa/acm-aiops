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

const getLayoutedElements = (
  nodes: Node[],
  edges: Edge[],
  direction: "TB" | "LR" = "LR"
) => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: direction });

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
      position: { x, y },
      targetPosition: Position.Left,
      sourcePosition: Position.Right,
    };
  });

  return { nodes: layoutedNodes, edges };
};

const StatusNode = ({ data }: NodeProps) => {
  const { label, status, message } = data;

  const base =
    "px-4 py-2 rounded-xl text-sm font-medium shadow border transition-all duration-200 text-center";

  const statusStyles: Record<string, string> = {
    finished: "bg-gray-100 text-gray-600 border-gray-200",
    activating: "bg-gray-100 text-gray-600 border-gray-200 animate-pulse",
    default: "bg-gray-100 text-gray-600 border-gray-200",
  };

  return (
    <div className="flex items-center space-x-2">
      <div className={`${base} ${statusStyles[status]}`}>{label}</div>
      {message && (
        <div
          className={`text-xs ${
            status === "activating" ? "animate-pulse text-gray-500" : "text-gray-500"
          }`}
        >
          {message}
        </div>
      )}
      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </div>
  );
};



const nodeTypes = {
  statusNode: StatusNode,
};

const baseNodes: Node[] = [
  {
    id: "1",
    type: "statusNode",
    data: { label: "✅ Finished", status: "finished" },
    position: { x: 0, y: 0 },
  },
  {
    id: "2",
    type: "statusNode",
    data: {
      label: "⏳ Processing",
      status: "activating",
      message: "Waiting for cluster status update...",
    },
    position: { x: 0, y: 0 },
  },
];

const baseEdges: Edge[] = baseNodes.slice(0, -1).map((node, index) => {
  const nextNode = baseNodes[index + 1];
  return {
    id: `e${node.id}-${nextNode.id}`,
    source: node.id,
    target: nextNode.id,
    animated: true,
    style: { stroke: "#cbd5e1" },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: "#94a3b8",
    },
    type: "smoothstep",
  };
});

export default function StatusGraph() {
  const { nodes: layoutedNodes, edges: layoutedEdges } = useMemo(
    () => getLayoutedElements(baseNodes, baseEdges, "LR"),
    []
  );

  const [nodes, , onNodesChange] = useNodesState(layoutedNodes);
  const [edges, , onEdgesChange] = useEdgesState(layoutedEdges);

  return (
    <ReactFlowProvider>
      <div className="w-full max-w-3xl h-[300px] mx-auto border border-gray-100 rounded-xl shadow-sm bg-white">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          fitView
          nodesDraggable={false}
          zoomOnScroll={false}
          panOnScroll
          panOnDrag
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
        >
          <Controls showZoom={false} showFitView={false} />
        </ReactFlow>
      </div>
    </ReactFlowProvider>
  );
}
