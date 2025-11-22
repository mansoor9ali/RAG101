import React, { useRef } from 'react';
import { Upload, FileText, CheckCircle, Loader2 } from 'lucide-react';
import clsx from 'clsx';

const FileUpload = ({ onUpload, status, fileName }) => {
    const fileInputRef = useRef(null);

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            onUpload(file);
        }
    };

    return (
        <div className="w-full">
            <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                className="hidden"
                accept=".pdf"
            />

            <div
                onClick={() => status !== 'uploading' && fileInputRef.current.click()}
                className={clsx(
                    "group border border-dashed rounded-lg p-8 flex flex-col items-center justify-center cursor-pointer transition-all duration-200",
                    status === 'uploading' ? "border-blue-300 bg-blue-50 cursor-wait" :
                        status === 'success' ? "border-green-300 bg-green-50" :
                            "border-gray-300 bg-white hover:border-blue-400 hover:bg-gray-50"
                )}
            >
                {status === 'uploading' ? (
                    <Loader2 className="w-8 h-8 text-blue-500 animate-spin mb-3" />
                ) : status === 'success' ? (
                    <CheckCircle className="w-8 h-8 text-green-500 mb-3" />
                ) : (
                    <div className="p-3 rounded-full bg-blue-50 text-blue-600 mb-3 group-hover:scale-110 transition-transform">
                        <Upload className="w-6 h-6" />
                    </div>
                )}

                <h3 className={clsx("text-sm font-medium mb-1", status === 'success' ? "text-green-700" : "text-slate-900")}>
                    {status === 'success' ? fileName : "Upload PDF Document"}
                </h3>
                <p className="text-xs text-slate-500">
                    {status === 'success' ? "Ready for processing" : "Click to browse or drag file here"}
                </p>
            </div>
        </div>
    );
};

export default FileUpload;
