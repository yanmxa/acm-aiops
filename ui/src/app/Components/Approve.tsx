"use client";
import React from "react";

export interface ApproveProps {
  content: string;
  onAnswer: (approved: boolean) => void;
  title?: string;
}

export const Approve: React.FC<ApproveProps> = ({
  content,
  onAnswer,
  title = "Do you approve?",
}) => {
  return (
    <div className="p-6 rounded-xl shadow-xl bg-white border border-gray-200 max-w-md mx-auto text-center space-y-4">
      <h2 className="text-2xl font-semibold text-gray-800">{title}</h2>
      <p className="text-gray-600">{content}</p>
      <div className="flex justify-center gap-4 mt-4">
        <button
          onClick={() => onAnswer(true)}
          className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition"
        >
          ✅ Approve
        </button>
        <button
          onClick={() => onAnswer(false)}
          className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition"
        >
          ❌ Reject
        </button>
      </div>
    </div>
  );
};
