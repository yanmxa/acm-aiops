from typing import List, Literal
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from langchain.tools import tool

from agent.utils.logging_config import get_logger

logger = get_logger("rechart_tool")


# Define the schema
class RechartData(BaseModel):
    rechart_data: List[object] = Field(
        description="The structured data used for rendering the chart with Recharts. Each item should be a dictionary with float metric values and no units."
    )
    rechart_type: Literal["BarChart", "LineChart"] = Field(
        description="The chart type to use. Supported values: 'BarChart' or 'LineChart'."
    )
    x_axis_key: str = Field(
        description="The key used for the x-axis (e.g., 'cluster')."
    )
    y_axis_keys: List[str] = Field(
        description="List of keys from each data point to plot on the y-axis (e.g., ['cpu', 'memory', 'battery', 'power'])."
    )
    unit: str = Field(
        description="The unit of measurement for y-axis values, such as 'MiB' or 'GiB' for memory, 'cores' or 'm' for CPU, 'J' or 'kJ' for energy consumption. The unit should be human-readable."
    )
    chart_title: str = Field(
        description="Title to display above the chart."
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
    """
    
    logger.info("render charts with data")
    print(data)
    
    # Logic can be replaced with actual rendering logic or chart generation engine
    return f"Received {len(data.charts)} chart(s) for rendering."
