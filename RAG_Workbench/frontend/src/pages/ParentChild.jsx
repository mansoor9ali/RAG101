import React, { useState } from 'react';
import { Layers, ArrowRight, Search, Maximize2, Minimize2, Sparkles } from 'lucide-react';
import FileUpload from '../components/FileUpload.jsx';
import EmbeddingVisualizer from '../components/EmbeddingVisualizer.jsx';

const ParentChild = () => {
    const [file, setFile] = useState(null);
    const [uploadStatus, setUploadStatus] = useState('idle');
    const [filePath, setFilePath] = useState(null);
    const [collectionName, setCollectionName] = useState(null);

    const [query, setQuery] = useState('');
    const [searching, setSearching] = useState(false);
    const [results, setResults] = useState(null); // { parents: [], children: [] }
    const [generating, setGenerating] = useState(false);
    const [answer, setAnswer] = useState(null);

    const handleUpload = async (uploadedFile) => {
        setUploadStatus('uploading');
        const formData = new FormData();
        formData.append('file', uploadedFile);

        try {
            const res = await fetch('http://localhost:8000/api/upload', { method: 'POST', body: formData });
            const data = await res.json();
            setFile(uploadedFile);
            setFilePath(data.file_path);
            setUploadStatus('success');

            // Auto-process with Parent-Child Indexing
            const procRes = await fetch('http://localhost:8000/api/process_pc', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_path: data.file_path }),
            });
            const procData = await procRes.json();
            setCollectionName(procData.collection_name);
        } catch (error) {
            console.error('Setup failed', error);
            setUploadStatus('idle');
        }
    };

    const handleSearch = async () => {
        if (!query || !collectionName) return;
        setSearching(true);
        setResults(null);
        setAnswer(null);

        try {
            const res = await fetch('http://localhost:8000/api/query_pc', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query,
                    collection_name: collectionName,
                    top_k: 3
                }),
            });
            const data = await res.json();
            setResults(data);
        } catch (error) {
            console.error('Search failed', error);
        } finally {
            setSearching(false);
        }
    };

    const handleGenerate = async () => {
        if (!results || !results.parents.length) return;
        setGenerating(true);
        setAnswer(null);

        try {
            // Use parent chunks for generation
            const contextChunks = results.parents.map(p => p.content);

            const res = await fetch('http://localhost:8000/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query,
                    context_chunks: contextChunks
                }),
            });
            const data = await res.json();
            setAnswer(data.answer);
        } catch (error) {
            console.error('Generation failed', error);
        } finally {
            setGenerating(false);
        }
    };

    return (
        <div className="space-y-8">
            <div>
                <h2 className="text-3xl font-bold mb-2">Parent-Child Chunking</h2>
                <p className="text-gray-400">Retrieve small, specific chunks (children) but return larger context (parents) for the LLM.</p>
            </div>

            {/* Setup */}
            {!collectionName && (
                <section className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
                    <h3 className="text-xl font-semibold mb-4">Setup Document</h3>
                    <FileUpload onUpload={handleUpload} status={uploadStatus} fileName={file?.name} />
                </section>
            )}

            {collectionName && (
                <div className="space-y-6">
                    {/* Search Input */}
                    <section className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
                        <div className="flex gap-2">
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Ask a specific question..."
                                className="flex-1 bg-gray-950 border border-gray-800 rounded-lg px-4 py-3 focus:outline-none focus:border-orange-500 transition-colors"
                                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                            />
                            <button
                                onClick={handleSearch}
                                disabled={searching || !query}
                                className="bg-orange-600 hover:bg-orange-500 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
                            >
                                {searching ? 'Searching...' : <><Search size={20} /> Search</>}
                            </button>
                        </div>
                    </section>

                    {/* Visualization */}
                    {results && (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {/* Left: Retrieved Children */}
                            <section className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
                                <div className="flex items-center gap-3 mb-4">
                                    <div className="p-2 bg-blue-500/20 rounded-lg text-blue-400">
                                        <Minimize2 size={20} />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-semibold">Retrieved Children</h3>
                                        <p className="text-xs text-gray-400">Small chunks matched by vector search</p>
                                    </div>
                                </div>

                                {results.query_embedding && (
                                    <div className="mb-4">
                                        <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Query Embedding</h4>
                                        <EmbeddingVisualizer embedding={results.query_embedding} height={30} />
                                    </div>
                                )}

                                <div className="space-y-4">
                                    {results.children.map((child, i) => (
                                        <div key={i} className="bg-gray-950 border border-blue-500/30 rounded-xl p-4 text-sm text-gray-300 relative">
                                            <div className="absolute top-2 right-2 text-xs font-mono text-blue-400 bg-blue-500/10 px-2 py-1 rounded">
                                                Score: {child.score.toFixed(3)}
                                            </div>
                                            {child.content}
                                        </div>
                                    ))}
                                </div>
                            </section>

                            {/* Right: Parent Context */}
                            <section className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 flex flex-col">
                                <div className="flex items-center gap-3 mb-4">
                                    <div className="p-2 bg-orange-500/20 rounded-lg text-orange-400">
                                        <Maximize2 size={20} />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-semibold">Parent Context</h3>
                                        <p className="text-xs text-gray-400">Full context sent to LLM</p>
                                    </div>
                                </div>

                                <div className="space-y-4 flex-1 mb-6">
                                    {results.parents.map((parent, i) => (
                                        <div key={i} className="bg-gray-950 border border-orange-500/30 rounded-xl p-4 text-sm text-gray-300">
                                            {parent.content}
                                        </div>
                                    ))}
                                </div>

                                {/* Generation Step */}
                                <div className="pt-6 border-t border-gray-800">
                                    {!answer && (
                                        <button
                                            onClick={handleGenerate}
                                            disabled={generating}
                                            className="w-full bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-500 hover:to-red-500 text-white px-6 py-3 rounded-xl font-medium transition-all shadow-lg shadow-orange-900/20 flex items-center justify-center gap-2"
                                        >
                                            {generating ? (
                                                <>
                                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                                    Generating Answer...
                                                </>
                                            ) : (
                                                <>
                                                    <Sparkles size={20} />
                                                    Generate Answer with Watsonx
                                                </>
                                            )}
                                        </button>
                                    )}

                                    {answer && (
                                        <div className="bg-gradient-to-br from-orange-900/30 to-red-900/30 border border-orange-500/30 rounded-xl p-6">
                                            <div className="flex items-center gap-3 mb-4 text-orange-300">
                                                <Sparkles size={24} />
                                                <h3 className="text-lg font-semibold">Generated Answer</h3>
                                            </div>
                                            <div className="prose prose-invert max-w-none">
                                                <p className="text-gray-200 leading-relaxed whitespace-pre-wrap">{answer}</p>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </section>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default ParentChild;
