"use client";
import React from "react";

import { Loader2 } from "lucide-react"; // or any spinner icon

interface ProgressBarProps {
  progress: number; // still in props if needed
  label?: string;
}

export default function ProgressBar({ label = "Processing" }: ProgressBarProps) {
  return (
    <div className="flex items-center space-x-2 text-sm font-medium text-gray-700 animate-pulse">
      <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
      <span>{label}</span>
    </div>
  );
}

