# Figma Design Plan

Target design: **Civic Strategy HUD**

This plan covers the first Figma delivery for the frontend design system and screen previews.

## Output Scope

### 1. Design Tokens

- Color tokens
- Gauge segment colors
- State colors
- Radius scale
- Spacing scale
- Basic text hierarchy

### 2. Major Components

- `SiteHeader`
- `CommandSearch`
- `HouseSegmentedControl`
- `FilterPanel`
- `RosterCard`
- `StatsCounter`
- `PowerSemicircleGauge`
- `MajorityMarker`
- `StatusChip`
- `PrimaryButton`
- `TextButton`
- `InfoPanel`
- `DataSourcePanel`

### 3. Screen Previews

- Top page: search box, House/Council semicircle gauges, counters, quick filters, roster preview
- Search results page: filter panel, keyword search, result cards, pagination
- Legislator detail page: profile header, source panel, basic data panel

## Figma Generation Script

Use:

- `scripts/figma/create_civic_strategy_hud.js`

The script creates a new page named `Civic Strategy HUD` in the target Figma file and adds:

- `Design Tokens / Color Palette`
- `Component Library / Major Components`
- `Screen Preview / Top Page`
- `Screen Preview / Search Results`
- `Screen Preview / Legislator Detail`

## Review Notes

- The first Figma pass is a design-system mockup, not a pixel-perfect production capture.
- Gauge colors are neutral categorical colors, not official party colors.
- The top page gauge data can remain placeholder until a stats endpoint is added.
- After frontend implementation, capture the running web pages into Figma and compare them with this design-system mockup.

## Efficiency Proposal

The fastest workflow is:

1. Generate the Figma design-system mockup from the script.
2. Build the frontend using the same tokens and component names.
3. Capture the live frontend screens into Figma.
4. Compare Figma mockup and live capture side by side.
5. Adjust the source code first, then regenerate or update Figma only where needed.
