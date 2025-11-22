import React from 'react';
import { NavLink } from 'react-router-dom';
import { Layers, Search, FileText, Settings, Database, GitBranch } from 'lucide-react';
import clsx from 'clsx';

const Sidebar = () => {
    const navItems = [
        { icon: Layers, label: 'Basic RAG', path: '/' },
        { icon: FileText, label: 'Docling Parsing', path: '/parsing' },
        { icon: Search, label: 'Reranking', path: '/rerank' },
        { icon: GitBranch, label: 'Query Expansion', path: '/expansion' },
        { icon: Database, label: 'Parent-Child', path: '/parent-child' },
        { icon: Settings, label: 'Settings', path: '/settings' },
    ];

    return (
        <div className="w-64 bg-slate-900 text-slate-300 h-screen flex flex-col border-r border-slate-800 flex-shrink-0">
            <div className="p-6 border-b border-slate-800">
                <h1 className="text-lg font-semibold text-white tracking-tight flex items-center gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    RAG Workbench
                </h1>
            </div>

            <nav className="flex-1 p-4 space-y-1">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            clsx(
                                'flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors duration-200',
                                isActive
                                    ? 'bg-slate-800 text-white'
                                    : 'hover:bg-slate-800/50 hover:text-white'
                            )
                        }
                    >
                        <item.icon size={18} className={clsx("opacity-70", { "text-blue-400 opacity-100": item.path === location.pathname })} />
                        <span>{item.label}</span>
                    </NavLink>
                ))}
            </nav>

            <div className="p-4 border-t border-slate-800">
                <div className="flex items-center gap-3 px-3 py-2">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
                        AI
                    </div>
                    <div className="text-xs">
                        <p className="text-white font-medium">Admin User</p>
                        <p className="text-slate-500">admin@example.com</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
