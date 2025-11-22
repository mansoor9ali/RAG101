import React, { useState } from 'react';
import { FileText, ArrowRight, Code, File as FileIcon } from 'lucide-react';
import FileUpload from '../components/FileUpload.jsx';

const Parsing = () => {
    const [file, setFile] = useState(null);
    const [uploadStatus, setUploadStatus] = useState('idle');
    const [filePath, setFilePath] = useState(null);

    const [converting, setConverting] = useState(false);
    const [markdown, setMarkdown] = useState('');

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

    const handleConvert = async () => {
        if (!filePath) return;
        setConverting(true);
        try {
            const res = await fetch('http://localhost:8000/api/convert', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_path: filePath }),
            });
            const data = await res.json();
            setMarkdown(data.markdown_content);
        } catch (error) {
            console.error('Conversion failed', error);
        } finally {
            setConverting(false);
        }
    };

    return (
        <div className="space-y-8 h-[calc(100vh-8rem)] flex flex-col">
            <div>
                <h2 className="text-3xl font-bold mb-2">Docling Parsing</h2>
                <p className="text-gray-400">Convert complex PDFs into clean, structured Markdown using Docling.</p>
            </div>

            {/* Step 1: Upload */}
            {!markdown && (
                <section className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 shrink-0">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-8 h-8 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center font-bold">1</div>
                        <h3 className="text-xl font-semibold">Upload Document</h3>
                    </div>

                    <div className="space-y-4">
                        <FileUpload onUpload={handleUpload} status={uploadStatus} fileName={file?.name} />
                        {uploadStatus === 'success' && (
                            <button
                                onClick={handleConvert}
                                disabled={converting}
                                className="w-full bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {converting ? 'Converting with Docling...' : <><FileText size={20} /> Convert to Markdown</>}
                            </button>
                        )}
                    </div>
                </section>
            )}

            {/* Step 2: Comparison View */}
            {markdown && (
                <div className="flex-1 flex gap-6 min-h-0">
                    {/* PDF View (Placeholder/Iframe) */}
                    <div className="flex-1 bg-gray-900 border border-gray-800 rounded-2xl p-4 flex flex-col">
                        <div className="flex items-center gap-2 mb-4 text-gray-400">
                            <FileIcon size={18} />
                            <span className="font-medium">Original PDF</span>
                        </div>
                        <div className="flex-1 bg-gray-800/50 rounded-xl flex items-center justify-center text-gray-500">
                            {/* In a real app, we'd use an iframe or PDF viewer here. 
                   For now, we'll just show a placeholder or the file name. */}
                            <div className="text-center">
                                <FileIcon size={48} className="mx-auto mb-2 opacity-50" />
                                <p>{file?.name}</p>
                                <p className="text-sm opacity-50">(PDF Preview)</p>
                            </div>
                        </div>
                    </div>

                    {/* Markdown View */}
                    <div className="flex-1 bg-gray-900 border border-gray-800 rounded-2xl p-4 flex flex-col">
                        <div className="flex items-center gap-2 mb-4 text-blue-400">
                            <Code size={18} />
                            <span className="font-medium">Docling Markdown</span>
                        </div>
                        <div className="flex-1 bg-gray-950 rounded-xl p-4 overflow-auto font-mono text-sm text-gray-300 whitespace-pre-wrap border border-gray-800">
                            {markdown}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Parsing;
