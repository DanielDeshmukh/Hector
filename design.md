# HECTOR Legal Intelligence Frontend - Design Specification

## Project Overview

**HECTOR** (Hard-RAG Legal Intelligence System) is a React-based frontend application designed for querying Indian legal information. The application serves as an interface for a legal RAG (Retrieval-Augmented Generation) pipeline that retrieves information from a curated library of Indian legal texts including the Indian Penal Code (IPC), Bharatiya Nyaya Sanhita (BNS), and CrPC. The system emphasizes zero-hallucination retrieval with verifiable citations.

### Key Technical Stack
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS with custom theme
- **Icons**: Lucide React
- **Animation**: CSS keyframes with Tailwind utilities

---

## Design System

### Color Palette

The application uses a sophisticated dark theme with warm gold accents suitable for legal/professional contexts:

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| `cream` (Background) | `#111315` | Primary background, creates the dark base |
| `charcoal` | `#1a1a1a` | Cards, input backgrounds, secondary surfaces |
| `gold` | `#c9a962` | Primary accent, buttons, active states |
| `gold-light` | `#e8d5a3` | Headings, highlighted text, primary text |
| `slate-custom` | `#2d3748` | Borders, dividers, secondary elements |
| `silver` | `#7d8a96` | Secondary text, icons, muted content |
| `success` | `#22c55e` | Completed states, high confidence |
| `warning` | `#f59e0b` | Warning states (not prominently used) |
| `error` | `#ef4444` | Error states (not prominently used) |
| `info` | `#3b82f6` | Information states (not prominently used) |

### Typography

| Font Family | Font Name | Usage |
|-------------|-----------|-------|
| `font-serif` | EB Garamond | Headings, logo, response text, document content |
| `font-sans` | Inter | UI elements, buttons, labels, body text |
| `font-mono` | JetBrains Mono | Source indices, code-like elements |

### Font Sizes (Tailwind Notation)
- Logo Title: `text-lg` to `text-3xl`
- Section Headers: `text-[10px]` with `uppercase tracking-[0.18em]`
- Body Text: `text-[13px]` to `text-[15px]`
- Labels: `text-[10px]` to `text-[11px]`
- Small Text: `text-[9px]` to `text-[10px]`

### Animations
- `fadeIn`: 0.3s ease-out with 6px upward translate
- `animate-pulse`: Gold pulsing dot during processing
- `animate-spin`: Rotating loader for active pipeline stage
- `animate-bounce`: Three bouncing dots for processing indicator
- `highlight-pulse`: 2s infinite pulse for document highlights

---

## Component Architecture

### 1. App.tsx (Root Component)

The main layout container that orchestrates all child components and manages application state.

#### Layout Structure
```
+------------------------------------------------------------------+
|  SIDEBAR  |  MAIN CONTENT AREA                         | PANEL  |
|           |  +------------------------------------------+ |        |
|  [Logo]   |  | TOP BAR: Status indicator               | |        |
|           |  +------------------------------------------+ |        |
|  [New]    |  |                                          | |        |
|           |  | CONTENT AREA:                            | |        |
|  History  |  |   - WelcomeScreen (idle)                 | |        |
|  List     |  |   - ProcessingIndicator (processing)     | |        |
|           |  |   - ResponseDisplay (responded)         | |        |
|           |  |                                          | |        |
|  [Stats]  |  +------------------------------------------+ |        |
|           |  | QUERY INPUT (fixed bottom)               | |        |
+-----------+--------------------------------------------+---------+
```

#### State Management
- `appState`: `"idle" | "processing" | "responded"`
- `sidebarCollapsed`: Boolean for sidebar toggle
- `currentResponse`: QueryResponse object or null
- `activeSourceId`: Currently selected source ID
- `activeSource`: SourceReference object for document panel
- `processingStage`: Number (0-3) for processing indicator
- `submittedQuery`: The query text that was submitted

#### Responsive Behavior
- Main content area shrinks when document panel is open: `max-w-[calc(100%-420px)]`
- Sidebar collapses from 280px to 56px
- Document panel width: 420px fixed

---

### 2. Sidebar Component

A collapsible left navigation panel containing branding, query controls, and history.

#### Dimensions
- **Expanded**: 280px width
- **Collapsed**: 56px width
- **Transition**: 300ms ease-in-out

#### Visual Structure

**Header Section**
- Logo container: 32x32px rounded-md with gold border
- Brand name "HECTOR" in EB Garamond serif font
- Subtitle "Legal Intelligence" in uppercase 10px tracking

**New Query Button**
- Full-width button with icon (Plus) and text
- Border: `border-slate-custom/60`
- Hover: gold border and subtle gold background

**Recent Queries Section**
- Section label: "RECENT QUERIES" in 10px uppercase
- List of query items with:
  - Domain icon (Gavel/FileText/BookOpen)
  - Query text (truncated)
  - Date in Indian locale format
  - Domain badge (Criminal/Procedural)
- Hover state: background color shift, gold text

**Footer Stats**
- "20+ Legal Texts Indexed"
- Online status indicator with green dot

**Collapse Toggle**
- Positioned at `-right-3` to float outside
- Circular button with chevron icon

---

### 3. QueryInput Component

The primary input interface for submitting legal queries, fixed at the bottom of the main content area.

#### Visual Elements

**Suggestion Chips (visible in idle state)**
- Display 4 sample legal queries as clickable chips
- Border: `border-slate-custom/50`
- Background: `bg-charcoal/50`
- Hover: gold border, gold text, gold-tinted background

**Textarea Area**
- Rounded corners: `rounded-xl`
- Background: `bg-charcoal/80`
- Border: `border-slate-custom/60`, focus: gold border
- Placeholder: "Enter your legal query — e.g., 'What is the BNS equivalent of IPC Section 302?'"
- Auto-resize: max-height 160px
- Font: 14.5px, gold-light text

**Bottom Action Bar**
- Attachment button (Paperclip icon) - currently non-functional
- Keyboard hint: "Enter to submit"
- Send button: gold background, charcoal icon

#### Interactions
- Enter key submits (without Shift)
- Shift+Enter for newline
- Disabled during processing state

---

### 4. WelcomeScreen Component

The initial landing screen displayed when the application is in idle state.

#### Layout Structure

**Logo & Title Section**
- Centered container
- Large logo icon (28px) in circular gold-bordered container
- Main title "HECTOR" in 3xl serif font
- Subtitle describing the system (max-width 432px)

**Feature Grid**
- 2x2 grid on larger screens, single column on mobile
- 4 feature cards explaining core system capabilities:
  1. **Intent Routing**: Query classification by legal domain
  2. **Hybrid Retrieval**: Dual-search semantic + keyword
  3. **Hierarchical Context**: Parent section/chapter resolution
  4. **Citation Grounding**: Source verification

**Feature Card Structure**
- Icon (18px) with gold tint
- Title: 13px medium weight
- Description: 11.5px, silver/40 color, leading-relaxed

**Disclaimer**
- Centered text at bottom
- 10.5px, silver/25 color
- Explains system limitations and non-legal-advice disclaimer

---

### 5. ProcessingIndicator Component

A visual display of the query processing pipeline stages shown during the "processing" state.

#### Processing Stages (4 stages total)
1. **Intent Routing** - Classifying legal domain
2. **Hybrid Retrieval** - Searching across legal texts
3. **Hierarchical Context** - Resolving parent sections
4. **Citation Grounding** - Verifying against source material

#### Visual States

**Active Stage** (currentStage === index)
- Background: `bg-gold/5`
- Border: `border-gold/20`
- Icon: gold color
- Text: gold-light
- Animated bouncing dots indicator

**Completed Stage** (index < currentStage)
- Opacity: 60%
- Icon: success color
- Text: silver/50
- "Done" label displayed

**Pending Stage** (index > currentStage)
- Opacity: 25%
- Icon: silver/30
- Text: silver/25

#### Stage Icons (Lucide)
- Intent Routing: Shield (15px)
- Hybrid Retrieval: Search (15px)
- Hierarchical Context: Layers (15px)
- Citation Grounding: FileCheck (15px)

#### Timing Simulation
- Stage 0: 800ms delay
- Stage 1: 1200ms delay
- Stage 2: 1000ms delay
- Stage 3: 900ms delay
- Response: 600ms after final stage

---

### 6. ResponseDisplay Component

The main content area displayed after a query has been processed and a response is available.

#### Sub-components & Elements

**Pipeline Status Bar**
- Section label: "CHAIN OF VERIFICATION" (10px uppercase)
- Horizontal flow of 4 stages with connecting lines
- Each stage shows status: completed/active/pending
- Tooltip on hover showing stage detail
- Responsive: text on desktop, icons on mobile

**Domain & Confidence Badges**
- Domain badge: gold border, gold text, tag icon
- Confidence badge: success border, success text, bar chart icon
- Timestamp: silver/30 color, Indian locale format

**Main Response Box**
- Rounded container with subtle border and background
- Content rendered with formatting:
  - Bold: `**text**` converted to strong gold-light
  - Italic: `*text*` converted to italic silver
  - Lists: `-` converted to gold-bullet list items

**Source Citations Section**
- Section label: "VERIFIED SOURCES (n)"
- Grid of clickable source cards

**Source Card Structure**
- Index number in circular badge (monospace)
- Book title (13px, gold-light when active)
- Author name (11px, silver/40)
- Matched text quote (11.5px, silver/50, 2-line clamp)
- Section info: icon + section name + page + paragraph
- Relevance score badge:
  - 95%+ = success (green)
  - 85-94% = gold (amber)
  - <85% = silver (gray)
- External link icon

#### Interactions
- Click on source card opens DocumentPanel
- Active source has gold border and background tint

---

### 7. DocumentPanel Component

A slide-in panel from the right side displaying the full source document with highlighted matching text.

#### Dimensions
- Width: 420px fixed
- Full height of viewport
- Slides in from right (no transition, instant mount)

#### Visual Structure

**Header**
- Source document label (10px uppercase, gold color)
- Book title (15px serif, gold-light)
- Author (11px, silver/40)
- Close button (X icon)

**Metadata Bar**
- Act name badge (e.g., "Indian Penal Code, 1860")
- Chapter information

**Section Navigation**
- Section name with book icon
- Page and paragraph info
- Highlight navigator: current/total matches
- Up/Down arrows to navigate between highlights

**Document Content Area**
- Styled to resemble legal document
- Font: EB Garamond serif, 14px
- Line height: 1.9
- Letter spacing: 0.01em
- Page divider with page number

**Highlighted Text**
- Background: `bg-gold/15`
- Left border: 2px gold/40
- Active highlight has pulsing animation
- Non-highlighted text: silver/70

**Footer**
- Relevance percentage
- Confidence badge (High/Moderate/Partial)

---

### 8. PipelineStatus Component

A compact horizontal display of the verification pipeline shown within ResponseDisplay.

#### Structure
- Container with border and subtle background
- Label: "CHAIN OF VERIFICATION" (10px uppercase)

**Stage Pills**
- Horizontal arrangement with connecting lines
- Each pill contains:
  - Status icon (Check/Loader/Circle)
  - Stage name (hidden on mobile)
  - Colored border based on status

**Status Types**
- Completed: success background/border, check icon
- Active: gold background/border, spinning loader
- Pending: slate background, hollow circle

**Tooltip**
- Appears on hover
- Contains stage name and detail text
- Positioned below with arrow pointer

---

## Page Layout & Flow

### Idle State (AppState: "idle")
1. Sidebar visible (expanded or collapsed)
2. Main content shows WelcomeScreen
3. Query input visible at bottom with suggestion chips
4. Top bar shows "Ready for queries"

### Processing State (AppState: "processing")
1. Top bar shows "Processing..." with gold pulsing dot
2. Main content shows:
   - Submitted query in styled container
   - ProcessingIndicator with current stage animated
3. Query input disabled with loading state
4. Sidebar remains accessible

### Responded State (AppState: "responded")
1. Top bar shows "Query Resolved" with green dot
2. Main content shows:
   - Query echo
   - PipelineStatus bar
   - Domain and confidence badges
   - Formatted response text
   - Source citations list
3. Query input remains available for new queries
4. DocumentPanel can be opened by clicking sources

---

## Responsive Breakpoints

The application uses Tailwind's default breakpoints. Key responsive behaviors:

- **Mobile (< 640px)**: PipelineStatus shows icons only, no text
- **All sizes**: Document panel is fixed 420px
- **Minimum width**: 320px supported (overflow hidden on smaller)

---

## Interaction Patterns

### Sidebar
- Click toggle button to collapse/expand
- Click query history item to re-submit that query
- Click "New Query" to reset to idle state

### Query Input
- Type in textarea (auto-grows)
- Click suggestion chip to populate textarea
- Press Enter to submit
- Click send button to submit

### Response Display
- Click source card to open DocumentPanel
- Click again to close (or click X in panel)
- Hover on pipeline stages for tooltips

### Document Panel
- Use up/down arrows to navigate highlights
- Click X or outside to close
- Scroll to read full document

---

## Data Structures

### QueryResponse Interface
```typescript
interface QueryResponse {
  id: string;
  query: string;
  answer: string;
  domain: string;
  confidence: number;
  sources: SourceReference[];
  pipeline: PipelineStage[];
  timestamp: string;
}
```

### SourceReference Interface
```typescript
interface SourceReference {
  id: string;
  bookTitle: string;
  author: string;
  chapter: string;
  section: string;
  page: number;
  paragraph: number;
  relevanceScore: number;
  matchedText: string;
  fullText: string;
  act: string;
  highlightRanges: { start: number; end: number }[];
}
```

### PipelineStage Interface
```typescript
interface PipelineStage {
  id: string;
  name: string;
  status: 'completed' | 'active' | 'pending';
  detail: string;
}
```

---

## Custom CSS Utilities

The following custom utilities are defined in index.css:

1. **Scrollbar styling**: 6px width, charcoal track, slate thumb
2. **Selection**: Gold background with light gold text
3. **Typing cursor**: blink animation for cursor elements
4. **Highlight pulse**: 2s infinite animation for document highlights
5. **Fade-in animations**: Multiple delay variants for staggered reveals

---

## Design Principles Applied

1. **Visual Hierarchy**: Gold accents guide attention to key actions and information
2. **Legal Professionalism**: Serif typography and muted palette convey authority
3. **Information Density**: Compact text sizes maximize information display
4. **Status Clarity**: Clear visual states for processing, completed, and active stages
5. **Verification Transparency**: Pipeline status and source citations build trust
6. **Reduced Cognitive Load**: Dark theme with strategic highlights reduces eye strain

---

## Component Hierarchy

```
App
├── Sidebar
│   ├── Logo/Brand
│   ├── New Query Button
│   ├── Query History List
│   ├── Footer Stats
│   └── Collapse Toggle
├── Main Content Area
│   ├── Top Bar (Status)
│   ├── Content Container
│   │   ├── WelcomeScreen (idle)
│   │   │   ├── Logo/Title
│   │   │   ├── Feature Grid
│   │   │   └── Disclaimer
│   │   ├── ProcessingIndicator (processing)
│   │   │   └── Stage List (4 stages)
│   │   └── ResponseDisplay (responded)
│   │       ├── PipelineStatus
│   │       ├── Domain/Confidence Badges
│   │       ├── Response Text
│   │       └── Source Citations
│   │           └── Source Cards
│   └── QueryInput
│       ├── Suggestion Chips
│       ├── Textarea
│       └── Action Bar
└── DocumentPanel (conditional)
    ├── Header
    ├── Metadata Bar
    ├── Section Navigation
    ├── Document Content
    └── Footer
```

---

## Notes for Implementation

1. The application simulates processing delays for demonstration purposes
2. All data is mocked - no actual API calls are made
3. The sidebar collapse animation uses CSS transitions
4. Document panel mounting is instant (no slide animation)
5. Processing stages are time-sequenced with setTimeout
6. Source highlighting uses character index ranges from mock data