# TravelWings — Design Reference

## Card Anatomy

Every card follows this pattern:
```
┌─────────────────────────────────────────┐
│  background: rgba(255,255,255,0.05)     │
│  border: 1px solid rgba(255,255,255,0.07)│
│  border-radius: 16px                     │
│  backdrop-filter: blur(12px)             │
│  box-shadow: 0 4px 24px rgba(0,0,0,0.2) │
│            + inset 0 1px 0 rgba(fff,0.04)│
│                                          │
│  :hover →                                │
│    background: rgba(255,255,255,0.07)    │
│    border-color: rgba(255,255,255,0.12)  │
│    transform: translateY(-1px)           │
│    box-shadow: enhanced                  │
└─────────────────────────────────────────┘
```

## Tag/Badge System

Tags are pill-shaped with colour-coded backgrounds:
```css
.tag {
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.7px;
  padding: 3px 8px;
  border-radius: 999px;
}
```

| Type       | Text Colour | Background              |
|------------|-------------|-------------------------|
| Departure  | --accent    | rgba(90,209,255,0.12)   |
| Transit    | --purple    | rgba(192,132,252,0.1)   |
| Arrival    | --green     | rgba(125,255,170,0.1)   |
| Return     | --orange    | rgba(255,122,89,0.12)   |
| Event      | --gold      | rgba(251,191,36,0.12)   |
| Essential  | --orange    | rgba(255,122,89,0.12)   |
| Confirmed  | --green     | rgba(125,255,170,0.1)   |
| Demo       | --muted     | rgba(255,255,255,0.05)  |

## Flight Card Expanded State

```
┌──────────────────────────────────────┐
│ [Logo] EK7 · Dubai → London    [Leg 1] ▶ │
├──────────────────────────────────────┤
│ Departure     01:20 DXB Terminal 3       │
│ Arrival       07:05 LHR Terminal 3       │
│ Duration      7h 45m                     │
│ Aircraft      Boeing 777-300ER           │
│ Class         Economy                    │
│ Booking       ABC123                     │
└──────────────────────────────────────┘
```

## Day Selector States

```css
/* Default */
.day-btn {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  min-width: 80px;
}

/* Active */
.day-btn.active {
  background: linear-gradient(135deg, rgba(125,255,170,0.1), rgba(90,209,255,0.06));
  border-color: rgba(125,255,170,0.25);
}

/* Event day (special) */
.day-btn.event {
  /* Add gold dot or star indicator */
}
```

## Checklist Item States

```css
/* Unchecked */
.check-item {
  padding: 8px 12px;
  border-bottom: 1px solid rgba(255,255,255,0.03);
  cursor: pointer;
  transition: all 0.2s;
}

/* Checked */
.check-item.done {
  opacity: 0.4;
  text-decoration: line-through;
}

/* Checkmark circle */
.check-circle {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid var(--dim);
  /* When done: background green, border green, white checkmark */
}
```

## SVG Route Map Pattern

```svg
<svg viewBox="0 0 900 200">
  <!-- Dark background -->
  <rect width="900" height="200" fill="#0d0d14"/>
  
  <!-- Grid dots -->
  <pattern id="dots">
    <circle r="0.5" fill="rgba(255,255,255,0.04)"/>
  </pattern>
  
  <!-- Flight path (dashed, animated) -->
  <path d="M x1,y1 Q cx,cy x2,y2" 
        stroke="url(#gradient)" 
        stroke-width="2" 
        stroke-dasharray="8,4"
        fill="none">
    <animate attributeName="stroke-dashoffset" 
             from="100" to="0" dur="3s" 
             repeatCount="indefinite"/>
  </path>
  
  <!-- Origin dot (pulsing) -->
  <circle cx="x1" cy="y1" r="5" fill="var(--accent)">
    <animate attributeName="r" values="5;7;5" dur="2s" repeatCount="indefinite"/>
  </circle>
  
  <!-- Destination dot -->
  <circle cx="x2" cy="y2" r="5" fill="var(--green)"/>
  
  <!-- City labels -->
  <text x="x1" y="y1+20" fill="var(--muted)" font-size="10">ORIGIN</text>
</svg>
```

## Ambient Orbs

Three fixed-position radial gradient blurs for background ambience:
```css
.orb {
  position: fixed;
  border-radius: 50%;
  filter: blur(140px);
  opacity: 0.22;
  pointer-events: none;
  z-index: 0;
}
/* Top-right: accent blue, 700x700 */
/* Bottom-left: orange, 550x550 */
/* Center: gold, 400x400 */
```

## Animated Plane Contrail

SVG plane with animated dash-offset trail:
```css
.contrail {
  fill: none;
  stroke: url(#trailGradient);
  stroke-width: 2;
  stroke-dasharray: 400;
  stroke-dashoffset: 400;
  animation: drawTrail 8s ease-in-out infinite;
}
@keyframes drawTrail {
  0%   { stroke-dashoffset: 400 }
  50%  { stroke-dashoffset: 0 }
  100% { stroke-dashoffset: -400 }
}
```

## Budget Table Pattern

```
┌──────────────────────────────────────┐
│ 💳 Cost Breakdown                    │
├──────────────────────────────────────┤
│ ✈️ Flights              £1,200       │
│ 🏨 Hotel (7 nights)     £840         │
│ 🍽️ Food & Drink         £350         │
│ 🚗 Transport             £150         │
│ 🎫 Activities            £200         │
│ 🐕 Pet sitting           £175         │
│──────────────────────────────────────│
│ Total                    £2,915       │
└──────────────────────────────────────┘
```

Values right-aligned, monospace font, accent colour on total.

## Responsive Breakpoints

```css
@media (max-width: 640px) {
  .stats { grid-template-columns: repeat(2, 1fr); }
  .pet-inner { flex-direction: column; text-align: center; }
  .banner-details { grid-template-columns: 1fr; }
  .flight-header { flex-direction: column; align-items: flex-start; }
}
```
