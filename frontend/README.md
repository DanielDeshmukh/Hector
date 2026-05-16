# HECTOR Frontend

Next.js 14 dashboard with "Lambo-Dark" theme for the HECTOR Legal Intelligence System.

## Quick Start

```bash
# Install dependencies (already done)
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Environment Variables

Create a `.env.local` file (already provided):

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=hector-dev-key
```

## Features

- **Dual-Pane Viewer**: AI Summary on the left, PDF Source on the right
- **Search History**: Track your search queries
- **Bookmarks**: Save important results
- **IPC ↔ BNS Comparator**: Compare old and new legal sections
- **High-Contrast Dark Theme**: Gold accents on dark background (#0a0a0a)

## Running with API

The frontend connects to the FastAPI backend. Start the API first:

```bash
uvicorn api.app:app --reload
```

Then start the frontend:

```bash
cd frontend
npm run dev
```

Access at: http://localhost:3000