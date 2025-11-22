# Frontend Fixes Applied

## Issues Fixed

### 1. Missing Tailwind CSS Configuration
**Problem:** The app was using Tailwind CSS v4 beta syntax but didn't have proper configuration files.

**Solution:**
- Created `tailwind.config.js` with proper content paths
- Created `postcss.config.js` with Tailwind and Autoprefixer plugins
- Downgraded Tailwind CSS from v4.1.17 to stable v3.4.1 in package.json
- Updated `index.css` to use standard Tailwind directives (`@tailwind base`, etc.)

### 2. React Router Bug in Sidebar
**Problem:** The Sidebar component was using `location.pathname` without importing the `useLocation` hook.

**Solution:**
- Added `useLocation` import from `react-router-dom`
- Added `const location = useLocation()` inside the Sidebar component

### 3. Dependencies Updated
**Changes made to package.json:**
- Removed `@tailwindcss/postcss` (v4 package)
- Changed `tailwindcss` from `^4.1.17` to `^3.4.1`
- Kept all other dependencies intact

## Files Created/Modified

### Created:
1. `tailwind.config.js` - Tailwind CSS configuration
2. `postcss.config.js` - PostCSS configuration for processing Tailwind
3. `FIXES_APPLIED.md` - This documentation file

### Modified:
1. `src/index.css` - Updated Tailwind directives
2. `src/components/Sidebar.jsx` - Fixed useLocation hook issue
3. `package.json` - Downgraded Tailwind CSS version

## How to Run the Application

### Prerequisites
- Node.js (v18 or higher recommended)
- npm or yarn

### Installation & Running

1. **Install dependencies:**
   ```bash
   cd F:\Projects\RAG101\RAG_APP\frontend
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

3. **Open your browser:**
   - Navigate to `http://localhost:5173`
   - The app should now render properly with all Tailwind styles applied

### Backend Requirements
The frontend expects a backend API running on `http://localhost:8000`. Make sure to:

1. Navigate to the backend directory:
   ```bash
   cd F:\Projects\RAG101\RAG_APP\backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start the backend server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

## Application Features

The RAG Workbench includes the following pages:

### 1. Basic RAG Pipeline (`/`)
- Upload PDF documents
- Process and chunk documents
- Vector similarity search
- LLM-based answer generation
- Embedding visualization

### 2. Docling Parsing (`/parsing`)
- Upload PDFs
- Convert to structured Markdown using Docling
- Side-by-side comparison view

### 3. Reranking Pipeline (`/rerank`)
- Initial retrieval (top 10 results)
- Cross-encoder reranking (top 5 results)
- Improved answer generation

### 4. Query Expansion (`/expansion`)
- LLM-based query expansion
- Multiple query variants
- Broader retrieval coverage

### 5. Parent-Child Chunking (`/parent-child`)
- Small chunks for precise retrieval
- Large parent context for generation
- Visual separation of children vs parents

## Technical Stack

- **React 19.2.0** - UI framework
- **React Router DOM 7.9.6** - Routing
- **Tailwind CSS 3.4.1** - Styling
- **Vite 7.2.2** - Build tool & dev server
- **Framer Motion 12.23.24** - Animations
- **Lucide React 0.553.0** - Icons
- **Axios 1.13.2** - HTTP client

## Troubleshooting

### Styles not loading
- Make sure `npm install` completed successfully
- Check that Tailwind CSS v3.4.1 is installed (not v4)
- Verify `tailwind.config.js` and `postcss.config.js` exist

### Sidebar navigation not working
- Check browser console for errors
- Verify React Router is installed correctly
- Ensure all page components exist in `src/pages/`

### API calls failing
- Verify backend is running on port 8000
- Check CORS settings in backend
- Inspect Network tab in browser DevTools

## Next Steps

To complete the application:

1. Verify backend API endpoints match frontend expectations
2. Test file upload functionality
3. Ensure document processing works end-to-end
4. Test all RAG techniques with real documents
5. Add error handling and loading states as needed

## Notes

- All components use Tailwind CSS utility classes
- The app uses a dark theme (gray-900 backgrounds)
- Inter font is loaded from Google Fonts
- Components are modular and reusable across pages

