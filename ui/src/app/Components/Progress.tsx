"use client";
import React, { useState } from "react";

import { SatelliteDish, CheckCircle, Circle, Activity } from "lucide-react";
import { Progress } from '../lib/agent_state';

interface ProgressBarProps {
  status: string;
  label?: string;
  progress?: Progress;
}

// Remove hardcoded NODE_LABELS since we get this info from backend

export default function ProgressBar({ 
  label = "Processing", 
  status = "complete", 
  progress 
}: ProgressBarProps) {
  // State for controlling details visibility - collapsed by default when completed
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Don't hide progress bar, show completion state
  if (!progress && status === "complete") {
    return <></>
  }

  if (!progress) {
    // Fallback to simple progress bar
    return (
      <div className="flex items-center space-x-2 text-sm font-medium text-gray-700 animate-pulse pl-1">
        <SatelliteDish size={16} />
        <span>{label}</span>
      </div>
    );
  }

  const { nodes } = progress;
  
  // Calculate progress percentage based on completed nodes
  const completedCount = nodes.filter(node => node.status === "completed").length;
  const activeCount = nodes.filter(node => node.status === "active").length;
  const totalCount = nodes.length;
  const progress_percentage = totalCount > 0 ? Math.round(((completedCount + activeCount * 0.5) / totalCount) * 100) : 0;
  
  const isWorkflowCompleted = completedCount === totalCount && totalCount > 0;
  
  // Auto-expand when workflow is in progress, collapse when completed
  const shouldAutoExpand = !isWorkflowCompleted;

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-3 mb-3">
      {/* Compact Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-3">
          {/* Progress Icon */}
          <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-slate-50 to-slate-100 rounded-lg flex items-center justify-center text-slate-600">
            <Activity className="w-4 h-4" />
          </div>
          
          <div className={`px-2 py-1 rounded text-xs font-medium ${
            isWorkflowCompleted 
              ? "bg-emerald-100 text-emerald-700" 
              : "bg-blue-100 text-blue-700"
          }`}>
            {progress_percentage}%
          </div>
        </div>
        
        {/* Toggle button */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="flex items-center space-x-1 text-xs text-slate-500 hover:text-slate-700 transition-colors px-2 py-1 rounded-md hover:bg-slate-50"
          >
            <span>{isExpanded ? "Hide details" : "Show details"}</span>
          </button>
          
          <div className="flex-shrink-0 w-6 h-6 bg-slate-100 hover:bg-slate-200 rounded-md flex items-center justify-center transition-colors cursor-pointer"
               onClick={() => setIsExpanded(!isExpanded)}>
            <span className="text-xs text-slate-500 hover:text-slate-700 transition-colors">
              {isExpanded ? "▲" : "▼"}
            </span>
          </div>
        </div>
      </div>
      
      {/* Compact Progress Bar */}
      <div className="w-full bg-gray-100 rounded-full h-2 mb-3">
        <div 
          className={`h-2 rounded-full transition-all duration-500 ${
            isWorkflowCompleted 
              ? "bg-gradient-to-r from-emerald-400 to-emerald-500" 
              : "bg-gradient-to-r from-blue-400 to-blue-500"
          }`}
          style={{ width: `${progress_percentage}%` }}
        ></div>
      </div>

      {/* Compact Status Summary - Always Visible */}
      <div className="flex items-center space-x-2 text-xs text-gray-600">
        {nodes.map((node, index) => {
          const isActive = node.status === "active";
          const isCompleted = node.status === "completed";
          const nodeColors = ["text-emerald-500", "text-blue-500", "text-purple-500", "text-orange-500"];
          const iconColor = nodeColors[index % nodeColors.length];

          return (
            <div key={index} className="flex items-center space-x-1">
              {isCompleted ? (
                <CheckCircle size={12} className={iconColor} />
              ) : isActive ? (
                <SatelliteDish size={12} className="text-blue-500 animate-pulse" />
              ) : (
                <Circle size={12} className="text-gray-300" />
              )}
              <span className="truncate max-w-20">{node.name}</span>
            </div>
          );
        })}
      </div>

      {/* Detailed Node Status - Collapsible */}
      {(isExpanded || shouldAutoExpand) && (
        <div className="mt-3 pt-3 border-t border-gray-100 space-y-2">
          {nodes.map((node, index) => {
            const isActive = node.status === "active";
            const isCompleted = node.status === "completed";

            const nodeColors = [
              { completed: "text-emerald-600", bg: "bg-emerald-50", icon: "text-emerald-500" },
              { completed: "text-blue-600", bg: "bg-blue-50", icon: "text-blue-500" },
              { completed: "text-purple-600", bg: "bg-purple-50", icon: "text-purple-500" },
              { completed: "text-orange-600", bg: "bg-orange-50", icon: "text-orange-500" },
            ];
            const colorScheme = nodeColors[index % nodeColors.length];

            return (
              <div key={index} className={`flex items-start space-x-3 p-2 rounded transition-all duration-200 ${
                isCompleted ? colorScheme.bg : 
                isActive ? "bg-blue-50" : 
                "bg-gray-50"
              }`}>
                <div className="flex-shrink-0 mt-0.5">
                  {isCompleted ? (
                    <CheckCircle size={14} className={colorScheme.icon} />
                  ) : isActive ? (
                    <SatelliteDish size={14} className="text-blue-500 animate-pulse" />
                  ) : (
                    <Circle size={14} className="text-gray-300" />
                  )}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className={`text-xs font-medium ${
                    isCompleted ? colorScheme.completed : 
                    isActive ? "text-blue-600" : 
                    "text-gray-500"
                  }`}>
                    {node.name}
                  </div>
                  <div className={`text-xs mt-0.5 ${
                    isCompleted ? colorScheme.completed.replace("600", "500") : 
                    isActive ? "text-blue-500" : 
                    "text-gray-400"
                  }`}>
                    {node.message}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}


