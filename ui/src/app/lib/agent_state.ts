
export type ActionState = {
  status: "pending" | "completed";  // default: "pending"
  approval: "y" | "n";              // default: "y"
  name: string;
  args: string;
  output: string;
};

export interface AgentState {
  hubKubeconfig: string;
  update: string;
  actions: ActionState[];
}