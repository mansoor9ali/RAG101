import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout.jsx';
import BasicRAG from './pages/BasicRAG.jsx';
import Reranking from './pages/Reranking.jsx';
import Parsing from './pages/Parsing.jsx';
import Expansion from './pages/Expansion.jsx';
import ParentChild from './pages/ParentChild.jsx';

// Placeholder components for now
const Placeholder = ({ title }) => (
  <div className="p-6 bg-gray-900 rounded-xl border border-gray-800">
    <h2 className="text-2xl font-bold mb-4">{title}</h2>
    <p className="text-gray-400">Coming soon...</p>
  </div>
);

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<BasicRAG />} />
          <Route path="parsing" element={<Parsing />} />
          <Route path="rerank" element={<Reranking />} />
          <Route path="expansion" element={<Expansion />} />
          <Route path="parent-child" element={<ParentChild />} />
          <Route path="settings" element={<Placeholder title="Settings" />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
