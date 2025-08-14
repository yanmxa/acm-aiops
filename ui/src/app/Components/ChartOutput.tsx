import React from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
} from "recharts";

interface RechartOutputProps {
  chart: {
    rechart_data: Record<string, any>[];
    rechart_type: "BarChart" | "LineChart";
    x_axis_key: string;
    y_axis_keys: string[];
    unit: string;
    chart_title: string;
  };
}

const truncateLabel = (label: string, maxLength = 15) =>
  label.length > maxLength ? `${label.slice(0, maxLength)}…` : label;

const formatTimestamp = (name: string, index: number, all: any[]) => {
  const date = new Date(name);
  const prevDate = index > 0 ? new Date(all[index - 1]?.name) : null;

  const isNewDay = !prevDate || date.toDateString() !== prevDate.toDateString();

  if (isNewDay) {
    return `${date.toLocaleDateString(undefined, {
      month: "short",
      day: "numeric",
    })} ${date.toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    })}`;
  }

  return date.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
};

const RechartOutput: React.FC<RechartOutputProps> = ({ chart }) => {
  const { rechart_data, rechart_type, x_axis_key, y_axis_keys, unit, chart_title } = chart;

  if (!Array.isArray(rechart_data) || rechart_data.length === 0) {
    return <p className="text-xs text-gray-500">No chart data available.</p>;
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-4">
      {/* Chart Header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex-shrink-0 w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-600">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <div className="text-sm font-medium text-gray-700">
          {chart_title}
        </div>
      </div>

      {/* Chart Content */}
      <div className="h-[32rem] w-full">
        <ResponsiveContainer width="100%" height="100%">
        {rechart_type === "BarChart" ? (
          <BarChart
            data={rechart_data}
            margin={{ top: 20, right: 30, left: 60, bottom: 80 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey={x_axis_key}
              tickFormatter={(label) => truncateLabel(label, 10)}
              textAnchor="end"
              angle={-45}
              height={80}
              interval={0}
            />
            <YAxis unit={unit} width={80} />
            <Tooltip />
            {y_axis_keys.map((key, i) => (
              <Bar
                key={key}
                dataKey={key}
                fill={`hsl(${(i * 60) % 360}, 70%, 50%)`}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        ) : (
          <LineChart
            data={rechart_data}
            margin={{ top: 20, right: 30, left: 60, bottom: 80 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey={x_axis_key}
              tickFormatter={(label, index) =>
                formatTimestamp(label, index, rechart_data)
              }
              textAnchor="end"
              angle={-45}
              interval={rechart_data.length > 48 ? 1 : 0}
              height={60}
            />
            <YAxis unit={unit} width={80} />
            <Tooltip />
            {y_axis_keys.map((key, index) => (
              <Line
                key={key}
                type="monotone"
                dataKey={key}
                stroke={`hsl(${(index * 60) % 360}, 70%, 50%)`}
                strokeWidth={2}
                dot={false}
              />
            ))}
          </LineChart>
        )}
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default React.memo(RechartOutput);


interface RechartChartData {
  rechart_data: Record<string, any>[];
  rechart_type: "BarChart" | "LineChart";
  x_axis_key: string;
  y_axis_keys: string[];
  unit: string;
  chart_title: string;
}

interface RechartCollectionProps {
  charts: RechartChartData[];
}


const isValidChart = (chart: any): chart is RechartChartData => {
  return (
    chart &&
    Array.isArray(chart.rechart_data) &&
    chart.rechart_data.length > 0 &&
    (chart.rechart_type === "BarChart" || chart.rechart_type === "LineChart") &&
    typeof chart.x_axis_key === "string" &&
    Array.isArray(chart.y_axis_keys) &&
    chart.y_axis_keys.length > 0 &&
    typeof chart.unit === "string" &&
    typeof chart.chart_title === "string"
  );
};


export const RechartCollection: React.FC<RechartCollectionProps> = ({ charts }) => {
  console.log("charts", charts)

   const validCharts = Array.isArray(charts)
    ? charts.filter(isValidChart)
    : [];

    if (validCharts.length === 0) {
      return <></>
    }

  return (
    <div className="w-full py-2 px-6">
      <div className="space-y-4">
        {validCharts.map((chart, index) => (
          <RechartOutput key={index} chart={chart} />
        ))}
      </div>
    </div>
  );
};
