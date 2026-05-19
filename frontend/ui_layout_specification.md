# UI Layout Specification: HECTOR Legal Intelligence Interface

This document specifies the structural layout, element positioning, and component relationships for implementing the legal intelligence application interface. 

---

## 1. Overall Page Layout
The interface uses a full-screen, split-pane layout divided into two primary structural sections: a fixed left sidebar and a flexible main content area.

* **Total Layout Space:** 100vw width, 100vh height (Overflow hidden on the body to ensure a contained app experience).
* **Split Ratio:** * **Sidebar Width:** Fixed width occupying approximately 15% to 20% of the total screen width.
    * **Main Content Area:** Flexible width occupying the remaining 80% to 85% of the screen width.

---

## 2. Left Sidebar Layout & Component Hierarchy
The sidebar acts as the primary navigation and history tracker. It is a vertically stacked container with explicit top, middle, and bottom sections.

### A. Sidebar Header (Top Alignment)
* **Brand Block:** Located at the top left corner.
    * **Elements:** A small square graphic icon/logo on the left, immediately followed by a two-line text element:
        * Line 1: Brand Title (Larger font size, bold).
        * Line 2: Brand Subtitle/Tagline (Smaller font size, all caps).
* **Collapse/Expand Toggle:** A small interactive button containing an arrow icon positioned at the upper right edge of the sidebar panel, allowing the user to minimize the sidebar.

### B. Navigation & History Area (Middle Alignment, Scrollable)
* **"New Query" Button:** * **Positioning:** Placed directly beneath the Brand Block, spanning the full width of the internal sidebar margins.
    * **Elements:** Contained within a distinct rectangular border with generous internal padding. It contains a plus (+) icon followed by the text "New Query".
* **Section Label:** * **Positioning:** Spaced slightly below the New Query button.
    * **Elements:** Small text in all caps reading "RECENT QUERIES".
* **Recent Queries List:**
    * **Structure:** A vertical stack of list items representing historical searches.
    * **Individual Item Layout:** Each item is a multi-line, clickable row:
        * **Left Column:** A small icon representing the query category (e.g., a gavel or a document sheet icon).
        * **Right Column (Stacked Text):**
            * Line 1: The query title text (truncated with an ellipsis if it exceeds the sidebar width).
            * Line 2: Secondary metadata row containing:
                * A timestamp/date string (preceded by a tiny clock icon).
                * A small, rectangular category tag/badge with rounded corners containing text indicating the legal domain (e.g., "CRIMINAL", "PROCEDURAL").

### C. Sidebar Footer (Bottom Alignment)
* **Positioning:** Fixed at the absolute bottom of the sidebar.
* **Elements:** A single horizontal row containing two pieces of status information pushed to opposite sides:
    * Left side text: Indexing status (e.g., "20+ Legal Texts Indexed").
    * Right side text: System availability metric accompanied by a small solid circle status indicator dot (e.g., "• Online").

---

## 3. Main Content Area Layout
The main area functions as a dynamic dashboard that adapts based on user queries. In its initial/empty state, it follows a vertically structured, centered, multi-row configuration.

### A. Top Status Header
* **Positioning:** Runs along the top boundary of the main content area.
* **Elements:** Two text elements pushed to the far edges:
    * Left-aligned text: Current operational status (e.g., "Ready for queries").
    * Right-aligned text: Technical infrastructure breadcrumbs or system identifiers separated by a delimiter (e.g., "System Architecture · Pipeline Name").

### B. Central Brand & Features Section
This block is centered both horizontally and vertically within the upper half of the main viewing pane.

* **Hero Logo:** A medium-sized square graphic icon centered at the top of this block.
* **System Title:** Large, bold text placed directly beneath the icon.
* **System Subtitle/Tagline:** A short, multi-line centered description paragraph explaining the system's capabilities, set in a smaller font size.
* **Feature Grid:**
    * **Structure:** Located below the tagline, configured as a 2x2 grid (two columns, two rows).
    * **Grid Item Components:** Each of the four feature cards consists of a rectangular container with internal padding and structural elements:
        * **Icon Column:** A small graphic icon positioned at the top-left or centered-left inside the card.
        * **Text Column:**
            * Heading: A bold title line specifying the feature name.
            * Description: 2-3 lines of smaller paragraph text explaining the feature functionality.

### C. Interactive Input Section (Bottom Alignment)
This section is anchored to the bottom half of the main content pane and handles user interaction.

* **Suggested Queries Row:**
    * **Positioning:** Placed directly above the main search container.
    * **Structure:** A 2x2 grid or responsive horizontal wrap containing small, pill-shaped clickable text chips. Each chip displays a sample legal question to assist the user.
* **Main Search Input Box:**
    * **Dimensions:** A wide, prominent rectangular text container centered horizontally. It spans approximately 50% to 60% of the total screen width, providing substantial vertical height for typing.
    * **Internal Layout & Elements:**
        * **Top Area:** Dynamic placeholder or active text string prompting the user with an example query format.
        * **Bottom Utility Bar (Inside the Input Box boundary):** A dedicated horizontal strip along the bottom edge containing:
            * **Left Side:** An attachment/paperclip icon for file uploads.
            * **Right Side:** A submit text indicator/shortcut prompt (e.g., "↵ to submit") positioned immediately beside a distinct, square-shaped action button containing a paper-airplane or arrow submission icon.
