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
  Legend,
} from "recharts";

interface RechartOutputProps {
  output: {
    data: any[];
    type: string;
    unit?: string;
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

const RechartOutput: React.FC<RechartOutputProps> = ({ output }) => {
  const { data, type, unit } = output;

  if (!Array.isArray(data) || data.length === 0) {
    return <p className="text-xs text-gray-500">No chart data available.</p>;
  }

  return (
    <div className="h-[28rem] w-full">
      <ResponsiveContainer width="100%" height="100%">
        {type === "snapshot" ? (
          <BarChart
            data={data}
            margin={{ top: 20, right: 40, left: 20, bottom: 20 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="name"
              tickFormatter={(name) => truncateLabel(name, 10)}
              textAnchor="end"
              angle={-45}
              height={80}
              interval={0}
            />
            <YAxis unit={unit} width={60} />
            <Tooltip />
            <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
          </BarChart>
        ) : (
          <LineChart
            data={data}
            margin={{ top: 40, right: 120, left: 20, bottom: 60 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="name"
              tickFormatter={(name, index) => formatTimestamp(name, index, data)}
              textAnchor="end"
              angle={-45}
              interval={data.length > 48 ? 1 : 0}
              height={60}
            />
            <YAxis unit={unit} width={80} />
            <Tooltip
              contentStyle={{
                // backgroundColor: "rgba(255, 255, 255, 0.8)",
                backgroundColor: "rgba(255, 255, 255, 0.8)", // 50% transparent white
                border: "none",
                borderRadius: 8,
                boxShadow: "0 0 8px rgba(0,0,0,0.1)",
                // fontSize: 12,
                backdropFilter: "blur(6px)", // adds a subtle blur behind tooltip
                WebkitBackdropFilter: "blur(6px)", // ensures Safari compatibility
                padding: "8px 12px",
              }}
              // itemStyle={{ color: "#333" }}
              // labelStyle={{ fontWeight: "bold", color: "#111" }}
            />
            {Object.keys(data[0])
              .filter((key) => key !== "name")
              .map((key, index) => (
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
