import React from 'react';

const EmbeddingVisualizer = ({ embedding, height = 40, className = "" }) => {
    if (!embedding || embedding.length === 0) return null;

    // Normalize values for visualization (assuming they are roughly -1 to 1, but we want 0-1 for color/opacity)
    // Embeddings are usually normalized, so values are small.
    // We'll map values to a color gradient.

    return (
        <div className={`flex flex-col gap-1 ${className}`}>
            <div className="text-xs text-gray-500 font-mono">Embedding Vector ({embedding.length} dims)</div>
            <div className="flex w-full overflow-hidden rounded-md bg-gray-900 border border-gray-700" style={{ height: `${height}px` }}>
                {embedding.slice(0, 100).map((val, idx) => {
                    // Map value (-0.1 to 0.1 approx for high dim) to color
                    // Let's just use opacity of a blue color for simplicity and "tech" look
                    // Normalize roughly: val is usually small.
                    const opacity = Math.min(Math.max((val + 0.1) * 5, 0.1), 1);
                    return (
                        <div
                            key={idx}
                            className="flex-1"
                            style={{
                                backgroundColor: `rgba(56, 189, 248, ${opacity})`, // Tailwind sky-400
                                borderRight: '1px solid rgba(0,0,0,0.1)'
                            }}
                            title={val.toFixed(4)}
                        />
                    );
                })}
            </div>
            <div className="flex justify-between text-[10px] text-gray-600 font-mono">
                <span>0</span>
                <span>...</span>
                <span>{embedding.length}</span>
            </div>
        </div>
    );
};

export default EmbeddingVisualizer;
