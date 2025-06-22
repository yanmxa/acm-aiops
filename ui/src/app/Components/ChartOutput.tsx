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
    <div className="h-[28rem] w-full">
      <h3 className="text-sm font-semibold text-slate-700 mb-2 text-center">{chart_title}</h3>
      <ResponsiveContainer width="100%" height="100%">
        {rechart_type === "BarChart" ? (
          <BarChart
            data={rechart_data}
            margin={{ top: 20, right: 40, left: 20, bottom: 20 }}
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
            <YAxis unit={unit} width={60} />
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
            margin={{ top: 40, right: 120, left: 20, bottom: 60 }}
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
      return <p className="text-sm text-gray-400">No valid charts to display.</p>;
    }

  return (
    <div className="space-y-8 mt-8">
      {validCharts.map((chart, index) => (
        <RechartOutput key={index} chart={chart} />
      ))}
    </div>
  );
};
