# HECTOR Frontend

Vite + React (JavaScript) + TailwindCSS frontend for the HECTOR Legal Intelligence System.

## Tech Stack

- **Build Tool**: Vite 5.x
- **Framework**: React 18
- **Styling**: TailwindCSS 4.x
- **State Management**: Zustand
- **Routing**: React Router DOM
- **Icons**: Lucide React

## Quick Start

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Environment Variables

Create a `.env` file:

```
VITE_API_URL=http://localhost:8000
VITE_API_KEY=hector-dev-key
```

## Features

- **Intent Routing**: Classifies queries by legal domain
- **Hybrid Retrieval**: Semantic + keyword search
- **Hierarchical Context**: Resolves parent sections
- **Citation Grounding**: Verifies against source material
- **Dark Theme**: Gold accents on dark charcoal background

## Running with HECTOR CLI

```bash
hector init
```

This automatically starts both the API server (port 8000) and frontend (port 3000).

Access at: http://localhost:3000