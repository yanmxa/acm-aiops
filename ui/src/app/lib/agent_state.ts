

export interface Node {
  name: string;
  status: "pending" | "active" | "completed" | "failed";
  message: string;
}

export interface State {
  query: string;
  progress?: Node[];
}


// rechart-params.ts
export const RechartParameters = [
  {
    name: "charts",
    type: "object[]",
    description: "Collection of charts with analysis and chart metadata.",
    required: true,
    items: {
      type: "object",
      attributes: [
        {
          name: "rechart_data",
          type: "object[]",
          description:
            "Structured data points for the chart. Each item is a key-value map of metrics (no units).",
          required: true,
          items: { type: "object" },
        },
        {
          name: "rechart_type",
          type: "string",
          description: "The chart type to use.",
          required: true,
          enum: ["BarChart", "LineChart"],
        },
        {
          name: "x_axis_key",
          type: "string",
          description: "The key used for the x-axis (e.g., 'cluster').",
          required: true,
        },
        {
          name: "y_axis_keys",
          type: "string[]",
          description:
            "List of keys from each data point to plot on the y-axis.",
          required: true,
        },
        {
          name: "unit",
          type: "string",
          description: "Unit of measurement for y-axis values after conversion (e.g., 'MiB', 'GiB').",
          required: true,
        },
        {
          name: "scaler",
          type: "number",
          description: "Scaling factor to convert raw data values to display unit. Default: 1.0.",
          required: false,
        },
        {
          name: "chart_title",
          type: "string",
          description: "Title to display above the chart.",
          required: true,
        },
      ],
    },
  },
];
