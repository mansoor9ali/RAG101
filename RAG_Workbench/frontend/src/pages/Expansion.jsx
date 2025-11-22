import React, { useState } from 'react';
import { Search, ArrowRight, ListPlus, CheckCircle, Sparkles } from 'lucide-react';
import FileUpload from '../components/FileUpload.jsx';
import ResultsDisplay from '../components/ResultsDisplay.jsx';
import EmbeddingVisualizer from '../components/EmbeddingVisualizer.jsx';

const Expansion = () => {
    const [file, setFile] = useState(null);
    const [uploadStatus, setUploadStatus] = useState('idle');
    const [filePath, setFilePath] = useState(null);
    const [collectionName, setCollectionName] = useState(null);

    const [query, setQuery] = useState('');
    const [expanding, setExpanding] = useState(false);
    const [expandedQueries, setExpandedQueries] = useState([]);
    const [results, setResults] = useState([]);
    const [queryEmbedding, setQueryEmbedding] = useState(null);
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

            // Auto-process for simplicity in this view
            const procRes = await fetch('http://localhost:8000/api/process', {
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

    const handleExpandAndSearch = async () => {
        if (!query || !collectionName) return;
        setExpanding(true);
        setExpandedQueries([]);
        setResults([]);
        setAnswer(null);

        try {
            // 1. Expand Query
            const expRes = await fetch('http://localhost:8000/api/expand', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query }),
            });
            const expData = await expRes.json();
            setExpandedQueries(expData.queries);

            // 2. Search for each query (simplified: just search for the first 3 combined or individually)
            // For visualization, let's just search using the original query + top expansion
            // In a real complex app, we'd fuse results (RRF). Here we'll just show the expansion effect.

            const searchRes = await fetch('http://localhost:8000/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: expData.queries.join(' '), // Naive combination for demo
                    collection_name: collectionName,
                    top_k: 5
                }),
            });
            const searchData = await searchRes.json();
            setResults(searchData.results);
            setQueryEmbedding(searchData.query_embedding);

        } catch (error) {
            console.error('Expansion failed', error);
        } finally {
            setExpanding(false);
        }
    };

    const handleGenerate = async () => {
        if (!results.length) return;
        setGenerating(true);
        setAnswer(null);

        try {
            // Use top 3 results for generation
            const contextChunks = results.slice(0, 3).map(r => r.content);

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
                <h2 className="text-3xl font-bold mb-2">Query Expansion</h2>
                <p className="text-gray-400">Use an LLM to generate multiple search queries to broaden retrieval coverage.</p>
            </div>

            {/* Setup */}
            {!collectionName && (
                <section className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
                    <h3 className="text-xl font-semibold mb-4">Setup Document</h3>
                    <FileUpload onUpload={handleUpload} status={uploadStatus} fileName={file?.name} />
                </section>
            )}

            {collectionName && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Left: Input & Expansion */}
                    <div className="lg:col-span-1 space-y-6">
                        <section className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
                            <h3 className="text-lg font-semibold mb-4">Original Query</h3>
                            <div className="space-y-4">
                                <input
                                    type="text"
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                    placeholder="Enter a complex question..."
                                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-4 py-3 focus:outline-none focus:border-blue-500 transition-colors"
                                />
                                <button
                                    onClick={handleExpandAndSearch}
                                    disabled={expanding || !query}
                                    className="w-full bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    {expanding ? 'Expanding...' : <><ListPlus size={20} /> Expand & Search</>}
                                </button>
                            </div>
                        </section>

                        {expandedQueries.length > 0 && (
                            <section className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
                                <h3 className="text-lg font-semibold mb-4 text-purple-400">Generated Queries</h3>
                                <div className="space-y-3">
                                    {expandedQueries.map((q, i) => (
                                        <div key={i} className="bg-gray-950 border border-gray-800 rounded-lg p-3 text-sm text-gray-300 flex items-start gap-3">
                                            <div className="mt-1 w-5 h-5 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center text-xs font-bold shrink-0">
                                                {i + 1}
                                            </div>
                                            {q}
                                        </div>
                                    ))}
                                </div>
                            </section>
                        )}
                    </div>

                    {/* Right: Results */}
                    <div className="lg:col-span-2">
                        <section className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 h-full">
                            <h3 className="text-lg font-semibold mb-4">Retrieval Results</h3>
                            {results.length > 0 ? (
                                <div className="space-y-4">
                                    {queryEmbedding && (
                                        <div className="mb-4">
                                            <h4 className="text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Combined Query Embedding</h4>
                                            <EmbeddingVisualizer embedding={queryEmbedding} height={30} />
                                        </div>
                                    )}
                                    <ResultsDisplay results={results} />

                                    {/* Generation Step */}
                                    <div className="mt-6 pt-6 border-t border-gray-800">
                                        {!answer && (
                                            <button
                                                onClick={handleGenerate}
                                                disabled={generating}
                                                className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white px-6 py-3 rounded-xl font-medium transition-all shadow-lg shadow-purple-900/20 flex items-center justify-center gap-2"
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
                                            <div className="bg-gradient-to-br from-purple-900/30 to-blue-900/30 border border-purple-500/30 rounded-xl p-6">
                                                <div className="flex items-center gap-3 mb-4 text-purple-300">
                                                    <Sparkles size={24} />
                                                    <h3 className="text-lg font-semibold">Generated Answer</h3>
                                                </div>
                                                <div className="prose prose-invert max-w-none">
                                                    <p className="text-gray-200 leading-relaxed whitespace-pre-wrap">{answer}</p>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ) : (
                                <div className="h-64 flex items-center justify-center text-gray-500 border-2 border-dashed border-gray-800 rounded-xl">
                                    Results will appear here
                                </div>
                            )}
                        </section>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Expansion;
