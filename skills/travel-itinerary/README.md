# TravelWings Skill

AI-powered travel itinerary generator that creates stunning, interactive HTML itineraries.

## Files

- **SKILL.md** — The skill prompt. Drop this into `.claude/skills/` or reference it when asking Claude to plan a trip.
- **DESIGN-REFERENCE.md** — Complete design system: colours, typography, components, animations, light/dark mode specs.
- **example-tokyo-trip.html** — Working example output. Open in any browser to see the full interactive experience.

## How It Works

1. Say `/travel` or "plan a trip to [destination]"
2. Claude asks about your trip details, then offers to check your **email**, **calendar**, **Google Drive**, **Notion**, and **Slack** for booking confirmations and event details
3. Claude gathers all the real data and generates a single self-contained HTML file
4. The output includes: animated hero, flight cards, day-by-day schedule, hotel cards, budget breakdown, interactive checklists (saved to localStorage), route map, event banners, and dark/light theme toggle

## Features

- Single HTML file, zero dependencies (except Google Fonts)
- Dark + light theme with toggle
- Interactive day selector
- Expandable flight cards
- Checklists persist via localStorage
- Animated SVG flight paths
- Glassmorphic card design
- Fully responsive
