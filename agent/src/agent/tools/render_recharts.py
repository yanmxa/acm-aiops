from typing import List, Literal, Dict, Any
from pydantic import BaseModel, Field
from langchain.tools import tool

from agent.utils.logging_config import get_logger

logger = get_logger("rechart_tool")

# Example data formats for reference:
"""
Example 1 - Bar Chart (Cluster Comparison):
{
  "rechart_data": [
    {"cluster": "local-cluster", "memory": 2048.5, "cpu": 0.85},
    {"cluster": "cluster1", "memory": 1024.2, "cpu": 0.42},
    {"cluster": "cluster2", "memory": 4096.8, "cpu": 1.23}
  ],
  "rechart_type": "BarChart",
  "x_axis_key": "cluster",
  "y_axis_keys": ["memory", "cpu"],
  "unit": "MiB (CPU: cores)",
  "chart_title": "Resource Usage by Cluster"
}

Example 2 - Line Chart (Time Series):
{
  "rechart_data": [
    {"timestamp": "2025-01-15T10:00:00Z", "memory": 1024, "cpu": 0.5},
    {"timestamp": "2025-01-15T10:05:00Z", "memory": 1100, "cpu": 0.6},
    {"timestamp": "2025-01-15T10:10:00Z", "memory": 950, "cpu": 0.45}
  ],
  "rechart_type": "LineChart", 
  "x_axis_key": "timestamp",
  "y_axis_keys": ["memory", "cpu"],
  "unit": "MiB (CPU: cores)",
  "chart_title": "Resource Usage Over Time"
}
"""


# Define the schema
class RechartData(BaseModel):
    rechart_data: List[Dict[str, Any]] = Field(
        description="REQUIRED: The structured data used for rendering the chart with Recharts. Each item should be a dictionary with metric values (raw numeric values from source data, string labels for x-axis). Example: [{'timestamp': 1755227795, 'cluster1:foo-client': 581467340.8, 'cluster2:foo-client': 557235855.36}]"
    )
    rechart_type: Literal["BarChart", "LineChart"] = Field(
        description="The chart type to use. 'BarChart' for categorical/comparison data, 'LineChart' for time-series or trend data."
    )
    x_axis_key: str = Field(
        description="The key used for the x-axis (e.g., 'cluster', 'timestamp', 'time'). Should match a field in each data point."
    )
    y_axis_keys: List[str] = Field(
        description="List of keys from each data point to plot on the y-axis (e.g., ['cpu', 'memory', 'energy']). Each key should correspond to numeric values in the data."
    )
    unit: str = Field(
        description="The unit of measurement for y-axis values after conversion. Use short, readable formats: 'MiB'/'GiB' for memory, 'cores'/'m' for CPU, 'J'/'kJ' for energy, 'W' for power, etc."
    )
    scaler: float = Field(
        default=1.0,
        description="The scaling factor to convert from raw data values to display unit. For example: bytes->MiB use 1/(1024*1024), cores->millicores use 1000, bytes->GiB use 1/(1024*1024*1024)."
    )
    chart_title: str = Field(
        description="Descriptive title for the chart that explains what is being visualized."
    )


class RechartDataCollection(BaseModel):
    charts: List[RechartData] = Field(
        description="Collection of charts with analysis and chart metadata."
    )

# LangChain Tool
@tool
def render_recharts(data: RechartDataCollection) -> str:
    """
    Render one or more Recharts visualizations based on the provided data and chart configuration.
    The chart data is passed to the frontend through tool call parameters, this function returns a status message.
    """
    
    logger.info(f"render_recharts called with {len(data.charts)} chart(s)")
    
    # Log the input data structure for debugging
    for i, chart in enumerate(data.charts):
        logger.debug(f"Chart {i+1} fields: {list(chart.__dict__.keys())}")
        if hasattr(chart, 'rechart_data'):
            logger.debug(f"Chart {i+1} has rechart_data with {len(chart.rechart_data)} data points")
        else:
            logger.error(f"Chart {i+1} missing rechart_data field!")
            logger.error(f"Chart {i+1} available fields: {list(chart.__dict__.keys())}")
    
    # Validate chart data
    valid_charts = 0
    chart_summaries = []
    
    for i, chart in enumerate(data.charts):
        try:
            # Validate required fields
            if not chart.rechart_data:
                logger.warning(f"Chart {i+1}: Empty data, skipping")
                continue
            
            # Basic validation
            if not chart.x_axis_key:
                logger.warning(f"Chart {i+1}: Missing x_axis_key")
                continue
                
            if not chart.y_axis_keys:
                logger.warning(f"Chart {i+1}: Missing y_axis_keys")
                continue
            
            # Validate data structure
            sample_point = chart.rechart_data[0] if chart.rechart_data else {}
            
            # Check if x_axis_key exists in data
            if chart.x_axis_key not in sample_point:
                logger.warning(f"Chart {i+1}: x_axis_key '{chart.x_axis_key}' not found in data. Available keys: {list(sample_point.keys())}")
                continue
            
            # Check if y_axis_keys exist in data  
            missing_keys = [key for key in chart.y_axis_keys if key not in sample_point]
            if missing_keys:
                logger.warning(f"Chart {i+1}: y_axis_keys {missing_keys} not found in data. Available keys: {list(sample_point.keys())}")
                # Log all data points to see if keys exist in other points
                logger.info(f"Chart {i+1}: All data points structure:")
                for idx, point in enumerate(chart.rechart_data[:3]):  # Show first 3 points
                    logger.info(f"  Point {idx+1}: {list(point.keys())}")
                continue
            
            valid_charts += 1
            chart_type = chart.rechart_type.replace("Chart", "").lower()
            chart_summaries.append(f"{chart_type} chart '{chart.chart_title}' ({len(chart.rechart_data)} data points)")
            logger.info(f"Chart {i+1}: '{chart.chart_title}' validated successfully")
            
        except Exception as e:
            logger.error(f"Error validating chart {i+1}: {e}")
            continue
    
    if valid_charts == 0:
        return "❌ No valid charts could be rendered. Please check the data format and field mappings."
    
    # Create summary message
    if valid_charts == 1:
        return f"✅ Successfully created 1 chart: {chart_summaries[0]}"
    else:
        summary = f"✅ Successfully created {valid_charts} charts:\n"
        for i, chart_summary in enumerate(chart_summaries, 1):
            summary += f"{i}. {chart_summary}\n"
        return summary.strip()
