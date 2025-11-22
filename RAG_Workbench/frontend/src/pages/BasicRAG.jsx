import React, { useState } from 'react';
import axios from 'axios';
import { Search, Database, Zap, ArrowRight } from 'lucide-react';
import FileUpload from '../components/FileUpload.jsx';
import ResultsDisplay from '../components/ResultsDisplay.jsx';
import EmbeddingVisualizer from '../components/EmbeddingVisualizer.jsx';

const BasicRAG = () => {
    const [file, setFile] = useState(null);
    const [collectionName, setCollectionName] = useState(null);
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [answer, setAnswer] = useState('');
    const [status, setStatus] = useState('idle'); // idle, uploading, processing, success, error
    const [stats, setStats] = useState(null);
    const [embeddingPreview, setEmbeddingPreview] = useState(null);
    const [queryEmbedding, setQueryEmbedding] = useState(null);

    const handleUpload = async (uploadedFile) => {
        setStatus('uploading');
        const formData = new FormData();
        formData.append('file', uploadedFile);

        try {
            const uploadRes = await axios.post('http://localhost:8000/api/upload', formData);
            const filePath = uploadRes.data.file_path;
            setFile(uploadedFile);

            setStatus('processing');
            const processRes = await axios.post('http://localhost:8000/api/process', {
                file_path: filePath,
                chunk_size: 1000,
                chunk_overlap: 200
            });

            setCollectionName(processRes.data.collection_name);
            setStats({
                numChunks: processRes.data.num_chunks,
                preview: processRes.data.preview_chunks
            });
            setEmbeddingPreview(processRes.data.embedding_preview);
            setStatus('success');
        } catch (error) {
            console.error("Error processing file:", error);
            setStatus('error');
        }
    };

    const handleSearch = async () => {
        if (!query || !collectionName) return;

        try {
            const res = await axios.post('http://localhost:8000/api/query', {
                query: query,
                collection_name: collectionName,
                top_k: 5
            });
            setResults(res.data.results);
            setQueryEmbedding(res.data.query_embedding);
            setAnswer(''); // Reset answer on new search
        } catch (error) {
            console.error("Error querying:", error);
        }
    };

    const handleGenerate = async () => {
        if (!query || results.length === 0) return;

        try {
            const contextChunks = results.map(r => r.content);
            const res = await axios.post('http://localhost:8000/api/generate', {
                query: query,
                context_chunks: contextChunks
            });
            setAnswer(res.data.answer);
        } catch (error) {
            console.error("Error generating answer:", error);
            setAnswer("Error generating answer. Please check backend logs.");
        }
    };

    return (
        <div className="space-y-8">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-slate-900">Basic RAG Pipeline</h2>
                <p className="text-slate-500 mt-1">Standard retrieval-augmented generation flow.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Controls */}
                <div className="lg:col-span-1 space-y-6">
                    {/* Upload Card */}
                    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
                        <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
                            <Database size={16} className="text-blue-600" />
                            Document Source
                        </h3>
                        <FileUpload onUpload={handleUpload} status={status} fileName={file?.name} />

                        {stats && (
                            <div className="mt-4 p-3 bg-slate-50 rounded border border-slate-100 text-xs text-slate-600 space-y-1">
                                <div className="flex justify-between">
                                    <span>Total Chunks:</span>
                                    <span className="font-medium text-slate-900">{stats.numChunks}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span>Collection:</span>
                                    <span className="font-mono text-slate-900">{collectionName?.substring(0, 12)}...</span>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Search Card */}
                    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
                        <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
                            <Search size={16} className="text-blue-600" />
                            Query
                        </h3>
                        <div className="space-y-3">
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Enter your question..."
                                className="w-full px-3 py-2 bg-white border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                                disabled={!collectionName}
                            />
                            <button
                                onClick={handleSearch}
                                disabled={!collectionName || !query}
                                className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                            >
                                <Search size={16} />
                                Retrieve Context
                            </button>
                        </div>
                    </div>
                </div>

                {/* Right Column: Results & Visualization */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Embeddings Visualization */}
                    {(embeddingPreview || queryEmbedding) && (
                        <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
                            <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
                                <Zap size={16} className="text-amber-500" />
                                Vector Embeddings
                            </h3>
                            <div className="space-y-6">
                                {embeddingPreview && (
                                    <EmbeddingVisualizer
                                        embedding={embeddingPreview}
                                        label="Document Chunk (Preview)"
                                        color="blue"
                                    />
                                )}
                                {queryEmbedding && (
                                    <EmbeddingVisualizer
                                        embedding={queryEmbedding}
                                        label="Query Vector"
                                        color="purple"
                                    />
                                )}
                            </div>
                        </div>
                    )}

                    {/* Results & Generation */}
                    {results.length > 0 && (
                        <div className="space-y-6">
                            <ResultsDisplay results={results} />

                            <div className="flex justify-center">
                                <button
                                    onClick={handleGenerate}
                                    className="group flex items-center gap-2 px-6 py-3 bg-slate-900 hover:bg-slate-800 text-white rounded-full font-medium transition-all shadow-lg hover:shadow-xl"
                                >
                                    <Zap size={18} className="text-yellow-400 group-hover:animate-pulse" />
                                    Generate Answer with LLM
                                    <ArrowRight size={16} className="opacity-50 group-hover:translate-x-1 transition-transform" />
                                </button>
                            </div>

                            {answer && (
                                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg border border-blue-100 p-6 shadow-sm">
                                    <h3 className="text-sm font-semibold text-blue-900 uppercase tracking-wider mb-3 flex items-center gap-2">
                                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                                        AI Answer
                                    </h3>
                                    <p className="text-slate-800 leading-relaxed whitespace-pre-wrap">
                                        {answer}
                                    </p>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default BasicRAG;
