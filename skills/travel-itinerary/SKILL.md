# TravelWings — AI Travel Itinerary Generator

> **Trigger:** `/travel`, "plan a trip", "create an itinerary", "travel planner", "build a trip plan"

## What This Skill Does

Generates a stunning, interactive HTML travel itinerary — a single self-contained file with dark/light theme toggle, animated flight paths, interactive day-by-day schedule, expandable flight cards, hotel/accommodation cards, event banners, pet care sections, SVG route maps, budget breakdowns, interactive checklists with localStorage persistence, and multi-trip navigation.

The output looks like a premium travel app — not a document. Think: dark glassmorphic cards, animated plane contrails, colour-coded flight tags, and smooth hover transitions.

---

## Setup Flow — CRITICAL

Before generating ANYTHING, Claude MUST run through this conversational discovery process. This is what makes the output magical — gathering real data from the user's actual life.

### Step 1: Basic Trip Details
Ask the user:
- **Where are you going?** (city/country)
- **What are the dates?** (departure → return)
- **Where are you flying from?** (home city)
- **Is this for a specific event?** (conference, wedding, business, holiday)
- **Who's going?** (solo, partner, family, group)

### Step 2: Integrations Check — Ask Every Time
Say something like: *"I can pull in real data to make this way more useful. Want me to check any of these?"*

- **📧 Email** — "Can I check your emails for flight confirmations, hotel bookings, or event tickets?"
- **📅 Calendar** — "Can I check your calendar for any events or meetings during those dates?"
- **📄 Google Drive / Docs** — "Do you have any trip docs, packing lists, or itineraries already saved?"
- **💬 Slack / Messages** — "Any group chats or threads with trip details I should look at?"
- **🔗 Any URLs** — "Got any booking confirmation links, event pages, or hotel URLs?"
- **📋 Notion** — "Any Notion pages with trip planning?"

If they say yes to any, use the appropriate MCP tools (Gmail, Google Calendar, Google Drive, Notion, etc.) to pull in real data.

### Step 3: Deep Details
Based on what you've gathered, ask about gaps:
- **Flights** — airline, flight numbers, times, terminals, layovers, seat class
- **Accommodation** — hotel name, address, check-in/out times, booking ref
- **Events** — event name, venue, schedule, any VIP/special access, dress code
- **Transport** — rental car, Uber, public transit, airport transfers
- **Pets** — pet name, sitter details, drop-off/pickup, special needs, vet info
- **Budget** — approximate costs for flights, hotel, food, activities, transport
- **Activities** — what they want to do each day, must-see spots, restaurants
- **Special requirements** — visa, travel insurance, medications, dietary needs

### Step 4: Confirm & Generate
Show a summary of everything you've gathered and confirm before building. Then generate the HTML.

---

## Design System — TravelWings

### Colour Palette
```css
:root {
  --bg: #06060a;           /* Deep space black */
  --surface: rgba(255,255,255,0.05);
  --surface-hover: rgba(255,255,255,0.07);
  --border: rgba(255,255,255,0.07);
  --border-hover: rgba(255,255,255,0.12);
  --accent: #5ad1ff;       /* Sky blue — primary */
  --accent-glow: rgba(90,209,255,0.12);
  --orange: #ff7a59;       /* Sunset orange — returns/warnings */
  --orange-glow: rgba(255,122,89,0.12);
  --green: #7dffaa;        /* Mint green — confirmations/go */
  --green-glow: rgba(125,255,170,0.1);
  --purple: #c084fc;       /* Lavender — transit/layovers */
  --purple-glow: rgba(192,132,252,0.1);
  --gold: #fbbf24;         /* Gold — events/VIP */
  --gold-glow: rgba(251,191,36,0.12);
  --text: #f0f0f5;
  --muted: #8a8a99;
  --dim: #50506a;
  --radius: 16px;
  --radius-sm: 10px;
}
```

### Typography
- **Font:** Inter (weights 300–900)
- **Mono:** system ui-monospace / Menlo (for times, codes)
- **Hero title:** clamp(32px, 6vw, 50px), weight 900, letter-spacing -2px
- **Section headers:** 16px, weight 800
- **Body:** 12–13px
- **Labels/tags:** 9–11px, uppercase, letter-spacing 1–2px, weight 600–700

### Component Library

#### 1. Hero Banner
Full-width with background image (or gradient fallback), gradient overlay from bottom, animated plane SVG with contrail, badge chip, large title, subtitle, traveller name.

#### 2. Event Banner
Gradient background with brand colours, logo, title with highlighted span, detail grid (2-col on desktop), optional hero image, expandable schedule with toggle.

#### 3. Flight Cards
Expandable cards with airline logo (base64 or URL), flight number + route as title, airline + date as subtitle. Colour-coded tags:
- `Leg 1/2/3` = accent blue / green / orange
- `Transit` = purple
- `Return` = orange
Expanded state shows: departure/arrival times, terminals, duration, aircraft, class, booking ref.

#### 4. Day Selector + Daily Schedule
Horizontal scrollable day buttons (Day 1, Day 2...) with date and subtitle. Active state has green border glow. Clicking loads that day's timeline into a content card below. Each day has:
- Title + subtitle
- Timeline items with monospace time + description
- Optional note at bottom

#### 5. Hotel Card
Horizontal card with logo, name (linked), description, and tag chip (e.g., "Recommended", "Booked").

#### 6. Pet Care Card
Card with pet photo (or emoji fallback), name, details, sitter info with green "Confirmed" badge.

#### 7. SVG Route Map
Dark background SVG showing flight path as animated dashed line between origin/destination dots. Legend below with colour-coded dots.

#### 8. Stats Bar
4-column grid (2 on mobile) with large coloured numbers and uppercase labels. E.g., "7 DAYS", "4 FLIGHTS", "2 EVENTS", "1 PET".

#### 9. Budget Breakdown
Card with table-style rows (label left, value right, monospace). Category grouping with subtotals. Total row at bottom with accent colour.

#### 10. Interactive Checklists
Grouped by category (Pre-Flight, Pet, Return Day). Each item is clickable toggle. Progress bar + counter (e.g., "3/9"). State persists via localStorage.

#### 11. Trip Footer
Multi-trip navigation with card links to other itineraries. Active trip highlighted. Each card has emoji icon, city name, dates, and status tag.

#### 12. Theme Toggle
Fixed position button (top-right). Toggles between dark and light mode. Light mode overrides all surface colours to white/cream with subtle shadows.

### Visual Effects
- **Orbs:** 3 fixed-position radial gradient blurs (accent, orange, gold) for ambient glow
- **Glassmorphism:** backdrop-filter: blur(12px) on cards + inset white border glow
- **Shimmer:** subtle left-to-right shimmer animation on banners
- **Hover lifts:** translateY(-1px) + enhanced box-shadow on hover
- **Animated plane:** SVG with dash-offset contrail animation
- **Pet image zoom:** scale(1.05) on parent hover

### Light Mode
Full light theme support via `body.light` class:
- Background: #f5f5f0
- Surfaces: rgba(255,255,255,0.7) with subtle shadows
- Text: #1a1a2e
- Muted: #555
- All accent colours preserved but with adjusted glows
- Cards get white background + border shadow

### Responsive
- Stats grid: 4 cols → 2 cols on mobile
- Pet card: row → column on mobile
- Flight header: row → column on mobile
- Banner details: 2 cols → 1 col on mobile
- Day selector: horizontal scroll with hidden scrollbar

### JavaScript Patterns
- **Day switcher:** Click day button → update content card via data attribute
- **Flight accordion:** Click to toggle `.on` class, max-height transition
- **Checklist persistence:** localStorage with trip-specific key
- **Theme toggle:** localStorage with trip-specific theme key
- **Progress bars:** Auto-calculated from checked items

---

## Output Format

Generate a single self-contained HTML file. All CSS inline in `<style>`. All JS inline in `<script>`. Images as base64 data URIs or emoji fallbacks. No external dependencies except Google Fonts (Inter).

Save as `travelwings-{destination}.html` on the user's Desktop.

---

## Example Sections to Include (adapt per trip)

1. Hero with destination image/gradient + animated plane
2. Event banner (if attending a specific event)
3. Stats bar (days, flights, events, etc.)
4. Route map (SVG)
5. Outbound flights (expandable cards)
6. Hotel/accommodation card
7. Pet care (if applicable)
8. Day-by-day schedule (interactive day selector)
9. Return flights (expandable cards)
10. Budget breakdown
11. Checklists (pre-flight, packing, return day, pet — as relevant)
12. Trip footer with navigation
13. Theme toggle (dark/light)

---

## Key Principles

1. **Real data > placeholder data.** Always try to pull from the user's actual emails, calendar, and docs first.
2. **Ask before assuming.** The setup conversation is what makes this valuable.
3. **One file, zero dependencies.** Everything self-contained.
4. **It should feel like a premium travel app**, not a document.
5. **Interactive > static.** Checklists save state. Days are clickable. Flights expand. Theme toggles.
6. **Colour-code everything.** Blue for outbound, green for confirmed, orange for return, purple for transit, gold for events.
