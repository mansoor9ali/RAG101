import React from 'react';
import { FileText, BarChart2 } from 'lucide-react';

const ResultsDisplay = ({ results }) => {
    if (!results || results.length === 0) return null;

    return (
        <div className="space-y-4">
            <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-3 flex items-center gap-2">
                <FileText size={16} className="text-slate-500" />
                Retrieved Context
            </h3>

            <div className="grid gap-4">
                {results.map((result, index) => (
                    <div
                        key={index}
                        className="bg-white rounded-lg border border-gray-200 p-5 shadow-sm hover:shadow-md transition-shadow duration-200"
                    >
                        <div className="flex justify-between items-start mb-3">
                            <div className="flex items-center gap-2">
                                <span className="bg-slate-100 text-slate-600 text-xs font-bold px-2 py-1 rounded">
                                    #{index + 1}
                                </span>
                                <span className="text-xs text-slate-400 font-mono">
                                    Source: {result.metadata?.source?.split('/').pop() || 'Unknown'}
                                </span>
                            </div>
                            <div className="flex items-center gap-1.5 text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded-full">
                                <BarChart2 size={12} />
                                Score: {result.score.toFixed(4)}
                            </div>
                        </div>

                        <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
                            {result.content}
                        </p>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ResultsDisplay;
