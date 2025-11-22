import React, { useState } from 'react';
import { Search, ArrowDownUp, Sparkles, CheckCircle } from 'lucide-react';
import FileUpload from '../components/FileUpload.jsx';
import ResultsDisplay from '../components/ResultsDisplay.jsx';
import EmbeddingVisualizer from '../components/EmbeddingVisualizer.jsx';

const Reranking = () => {
    const [file, setFile] = useState(null);
    const [uploadStatus, setUploadStatus] = useState('idle');
    const [filePath, setFilePath] = useState(null);

    const [processing, setProcessing] = useState(false);
    const [collectionName, setCollectionName] = useState(null);

    const [query, setQuery] = useState('');
    const [searching, setSearching] = useState(false);
    const [initialResults, setInitialResults] = useState([]);

    const [reranking, setReranking] = useState(false);
    const [rerankedResults, setRerankedResults] = useState([]);
    const [queryEmbedding, setQueryEmbedding] = useState(null);
    const [generating, setGenerating] = useState(false);
    const [answer, setAnswer] = useState(null);

    const handleUpload = async (uploadedFile) => {
        setUploadStatus('uploading');
        const formData = new FormData();
        formData.append('file', uploadedFile);

        try {
            const res = await fetch('http://localhost:8000/api/upload', {
                method: 'POST',
                body: formData,
            });
            const data = await res.json();
            setFile(uploadedFile);
            setFilePath(data.file_path);
            setUploadStatus('success');
        } catch (error) {
            console.error('Upload failed', error);
            setUploadStatus('idle');
        }
    };

    const handleProcess = async () => {
        if (!filePath) return;
        setProcessing(true);
        try {
            const res = await fetch('http://localhost:8000/api/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_path: filePath }),
            });
            const data = await res.json();
            setCollectionName(data.collection_name);
        } catch (error) {
            console.error('Processing failed', error);
        } finally {
            setProcessing(false);
        }
    };

    const handleSearch = async () => {
        if (!query || !collectionName) return;
        setSearching(true);
        setRerankedResults([]); // Reset reranked results
        setAnswer(null); // Reset answer on new search
        try {
            const res = await fetch('http://localhost:8000/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query,
                    collection_name: collectionName,
                    top_k: 10 // Retrieve more for reranking
                }),
            });
            const data = await res.json();
            setInitialResults(data.results);
        } catch (error) {
            console.error('Search failed', error);
        } finally {
            setSearching(false);
        }
    };

    const handleRerank = async () => {
        if (initialResults.length === 0) return;
        setReranking(true);
        try {
            const res = await fetch('http://localhost:8000/api/rerank', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query,
                    initial_results: initialResults,
                    top_k: 5
                }),
            });
            const data = await res.json();
            setRerankedResults(data.results);
            setQueryEmbedding(data.query_embedding);
            setAnswer(null); // Reset answer on new rerank
        } catch (error) {
            console.error('Reranking failed', error);
        } finally {
            setReranking(false);
        }
    };

    const handleGenerate = async () => {
        if (!rerankedResults.length) return;
        setGenerating(true);
        setAnswer(null);

        try {
            // Use top 3 reranked results for generation
            const contextChunks = rerankedResults.slice(0, 3).map(r => r.content);

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
                <h2 className="text-3xl font-bold mb-2">Reranking Pipeline</h2>
                <p className="text-gray-400">Improve retrieval quality by re-scoring initial results with a Cross-Encoder.</p>
            </div>

            {/* Step 1: Upload & Process (Simplified) */}
            <section className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-8 h-8 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold">1</div>
                    <h3 className="text-xl font-semibold">Setup</h3>
                </div>

                {!collectionName ? (
                    <div className="space-y-4">
                        <FileUpload onUpload={handleUpload} status={uploadStatus} fileName={file?.name} />
                        {uploadStatus === 'success' && (
                            <button
                                onClick={handleProcess}
                                disabled={processing}
                                className="w-full bg-purple-600 hover:bg-purple-500 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50"
                            >
                                {processing ? 'Processing...' : 'Process Document'}
                            </button>
                        )}
                    </div>
                ) : (
                    <div className="flex items-center gap-2 text-green-400 bg-green-400/10 p-4 rounded-lg border border-green-400/20">
                        <CheckCircle size={20} />
                        <span>Document ready for reranking experiments</span>
                    </div>
                )}
            </section>

            {/* Step 2: Initial Retrieval */}
            {collectionName && (
                <section className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-bold">2</div>
                        <h3 className="text-xl font-semibold">Initial Retrieval (Top 10)</h3>
                    </div>

                    <div className="flex gap-2 mb-6">
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Ask a question..."
                            className="flex-1 bg-gray-950 border border-gray-800 rounded-lg px-4 py-3 focus:outline-none focus:border-emerald-500 transition-colors"
                            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                        />
                        <button
                            onClick={handleSearch}
                            disabled={searching || !query}
                            className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50"
                        >
                            {searching ? 'Searching...' : 'Search'}
                        </button>
                    </div>

                    <ResultsDisplay results={initialResults} />
                </section>
            )}

            {/* Step 3: Reranking */}
            {initialResults.length > 0 && (
                <section className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 ring-1 ring-orange-500/30">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-orange-500/20 text-orange-400 flex items-center justify-center font-bold">3</div>
                            <h3 className="text-xl font-semibold">Reranking (Top 5)</h3>
                        </div>
                        <button
                            onClick={handleRerank}
                            disabled={reranking}
                            className="flex items-center gap-2 bg-orange-600 hover:bg-orange-500 text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
                        >
                            {reranking ? 'Reranking...' : <><ArrowDownUp size={18} /> Rerank Results</>}
                        </button>
                    </div>

                    <ResultsDisplay results={rerankedResults} />
                </section>
            )}

            {/* Step 4: Generation */}
            {rerankedResults.length > 0 && (
                <section className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-8 h-8 rounded-full bg-pink-500/20 text-pink-400 flex items-center justify-center font-bold">4</div>
                        <h3 className="text-xl font-semibold">Generation (Reranked Context)</h3>
                    </div>

                    {queryEmbedding && (
                        <div className="mb-6">
                            <h4 className="text-sm font-semibold text-gray-400 mb-3 uppercase tracking-wider">Query Embedding</h4>
                            <EmbeddingVisualizer embedding={queryEmbedding} className="mb-4" />
                        </div>
                    )}

                    {!answer ? (
                        <button
                            onClick={handleGenerate}
                            disabled={generating}
                            className="flex items-center gap-2 bg-pink-600 hover:bg-pink-500 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {generating ? (
                                <>Generating Answer...</>
                            ) : (
                                <>
                                    <Sparkles size={20} />
                                    Generate Answer
                                </>
                            )}
                        </button>
                    ) : (
                        <div className="bg-gray-950 border border-gray-800 rounded-xl p-6">
                            <div className="flex items-center gap-2 text-pink-400 mb-4">
                                <Sparkles size={20} />
                                <h4 className="font-semibold">Generated Answer</h4>
                            </div>
                            <p className="text-gray-300 leading-relaxed whitespace-pre-wrap">{answer}</p>
                        </div>
                    )}
                </section>
            )}
        </div>
    );
};

export default Reranking;
