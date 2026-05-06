// Figma Plugin API script for the ウシガー "Civic Strategy HUD" design.
// Run this through the Figma connector's use_figma tool after a target file key is available.

const TOKENS = {
  colors: {
    "bg/canvas": "#070A12",
    "bg/surface": "#101622",
    "bg/surface-raised": "#172033",
    "bg/command": "#0B1020",
    "line/subtle": "#243049",
    "line/strong": "#3D4D72",
    "text/primary": "#F2F6FF",
    "text/secondary": "#AAB8D8",
    "text/muted": "#6F7E9E",
    "accent/cyan": "#38D5FF",
    "accent/lime": "#A7F83B",
    "accent/amber": "#FFBE3D",
    "accent/rose": "#FF4F7B",
    "neutral/white": "#FFFFFF",
    "gauge/1": "#38D5FF",
    "gauge/2": "#A7F83B",
    "gauge/3": "#FFBE3D",
    "gauge/4": "#B985FF",
    "gauge/5": "#FF6B45",
    "gauge/6": "#35E0A1",
    "gauge/7": "#6F8CFF",
    "gauge/8": "#F36BCE",
    "gauge/other": "#65708A",
    "gauge/track": "#1E2A40",
    "gauge/majority": "#FFFFFF"
  },
  radius: {
    panel: 8,
    control: 6,
    chip: 999
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 12,
    lg: 16,
    xl: 24,
    xxl: 32
  }
};

const C = TOKENS.colors;

function rgb(hex) {
  const v = hex.replace("#", "");
  return {
    r: parseInt(v.slice(0, 2), 16) / 255,
    g: parseInt(v.slice(2, 4), 16) / 255,
    b: parseInt(v.slice(4, 6), 16) / 255
  };
}

function solid(hex, opacity = 1) {
  return [{ type: "SOLID", color: rgb(hex), opacity }];
}

async function loadFonts() {
  await figma.loadFontAsync({ family: "Inter", style: "Regular" });
  await figma.loadFontAsync({ family: "Inter", style: "Medium" });
  await figma.loadFontAsync({ family: "Inter", style: "Semi Bold" });
  await figma.loadFontAsync({ family: "Inter", style: "Bold" });
}

function text(label, size = 14, color = C["text/primary"], weight = "Regular") {
  const node = figma.createText();
  node.fontName = { family: "Inter", style: weight };
  node.fontSize = size;
  node.characters = label;
  node.fills = solid(color);
  node.lineHeight = { unit: "PERCENT", value: 130 };
  return node;
}

function frame(name, x, y, w, h, fill = C["bg/surface"]) {
  const node = figma.createFrame();
  node.name = name;
  node.x = x;
  node.y = y;
  node.resize(w, h);
  node.fills = solid(fill);
  node.strokes = solid(C["line/subtle"]);
  node.strokeWeight = 1;
  node.cornerRadius = TOKENS.radius.panel;
  node.clipsContent = false;
  return node;
}

function autoFrame(name, x, y, w, direction = "VERTICAL", gap = 12, padding = 16) {
  const node = frame(name, x, y, w, 100);
  node.layoutMode = direction;
  node.itemSpacing = gap;
  node.paddingTop = padding;
  node.paddingRight = padding;
  node.paddingBottom = padding;
  node.paddingLeft = padding;
  node.primaryAxisSizingMode = "AUTO";
  node.counterAxisSizingMode = "FIXED";
  return node;
}

function button(label, variant = "primary") {
  const node = figma.createFrame();
  node.name = `Button / ${label}`;
  node.layoutMode = "HORIZONTAL";
  node.primaryAxisSizingMode = "AUTO";
  node.counterAxisSizingMode = "AUTO";
  node.paddingTop = 10;
  node.paddingRight = 16;
  node.paddingBottom = 10;
  node.paddingLeft = 16;
  node.cornerRadius = TOKENS.radius.control;
  node.itemSpacing = 8;
  node.fills = solid(variant === "primary" ? C["accent/cyan"] : C["bg/surface-raised"], variant === "primary" ? 0.95 : 1);
  node.strokes = solid(variant === "primary" ? C["accent/cyan"] : C["line/subtle"]);
  node.appendChild(text(label, 14, variant === "primary" ? C["bg/canvas"] : C["text/primary"], "Semi Bold"));
  return node;
}

function chip(label, active = false) {
  const node = figma.createFrame();
  node.name = `Chip / ${label}`;
  node.layoutMode = "HORIZONTAL";
  node.primaryAxisSizingMode = "AUTO";
  node.counterAxisSizingMode = "AUTO";
  node.paddingTop = 7;
  node.paddingRight = 12;
  node.paddingBottom = 7;
  node.paddingLeft = 12;
  node.cornerRadius = TOKENS.radius.chip;
  node.fills = solid(active ? "#102B3A" : C["bg/surface-raised"]);
  node.strokes = solid(active ? C["accent/cyan"] : C["line/subtle"]);
  node.appendChild(text(label, 12, active ? C["text/primary"] : C["text/secondary"], "Medium"));
  return node;
}

function input(label, w = 520) {
  const node = figma.createFrame();
  node.name = "Input";
  node.resize(w, 44);
  node.cornerRadius = TOKENS.radius.control;
  node.fills = solid(C["bg/canvas"]);
  node.strokes = solid(C["line/strong"]);
  const copy = text(label, 14, C["text/muted"]);
  copy.x = 14;
  copy.y = 13;
  node.appendChild(copy);
  return node;
}

function stat(label, value) {
  const node = frame(`StatsCounter / ${label}`, 0, 0, 148, 84, C["bg-surface-raised"] || C["bg/surface-raised"]);
  node.layoutMode = "VERTICAL";
  node.paddingTop = 12;
  node.paddingRight = 14;
  node.paddingBottom = 12;
  node.paddingLeft = 14;
  node.itemSpacing = 6;
  node.appendChild(text(label, 12, C["text/secondary"], "Medium"));
  node.appendChild(text(value, 28, C["text/primary"], "Bold"));
  return node;
}

function rosterCard(name, meta) {
  const node = autoFrame(`RosterCard / ${name}`, 0, 0, 340, "VERTICAL", 8, 14);
  node.fills = solid(C["bg/surface-raised"]);
  node.appendChild(text(name, 18, C["text/primary"], "Semi Bold"));
  node.appendChild(text(meta, 13, C["text/secondary"]));
  node.appendChild(button("詳細", "secondary"));
  return node;
}

function createGauge(parent, name, x, y, w, ruling, majority, total) {
  const panel = frame(`PowerSemicircleGauge / ${name}`, x, y, w, 252, C["bg/surface"]);
  parent.appendChild(panel);

  const title = text(`${name} 勢力図`, 18, C["text/primary"], "Semi Bold");
  title.x = 18;
  title.y = 16;
  panel.appendChild(title);

  const centerX = w / 2;
  const centerY = 172;
  const radius = Math.min(w * 0.34, 128);
  const colors = [C["gauge/1"], C["gauge/2"], C["gauge/3"], C["gauge/4"], C["gauge/5"], C["gauge/6"], C["gauge/7"]];
  let angle = 180;
  const portions = [0.42, 0.28, 0.13, 0.08, 0.04, 0.03, 0.02];

  for (let s = 0; s < portions.length; s++) {
    const steps = Math.max(4, Math.round(portions[s] * 30));
    for (let i = 0; i < steps; i++) {
      const a = angle + (180 * portions[s] * i) / steps;
      const rad = (Math.PI * a) / 180;
      const tick = figma.createRectangle();
      tick.name = `Gauge arc ${s + 1}`;
      tick.resize(10, 9);
      tick.cornerRadius = 5;
      tick.fills = solid(colors[s]);
      tick.x = centerX + radius * Math.cos(rad) - 5;
      tick.y = centerY + radius * Math.sin(rad) - 5;
      tick.rotation = a + 90;
      panel.appendChild(tick);
    }
    angle += 180 * portions[s];
  }

  const marker = figma.createLine();
  marker.name = "MajorityMarker";
  marker.x = centerX;
  marker.y = centerY - radius - 18;
  marker.resize(0, radius + 14);
  marker.strokes = solid(C["gauge/majority"]);
  marker.strokeWeight = 2;
  panel.appendChild(marker);

  const markerLabel = text("過半数ライン", 11, C["text/secondary"], "Medium");
  markerLabel.x = centerX - 42;
  markerLabel.y = centerY - radius - 38;
  panel.appendChild(markerLabel);

  const summary = text(`与党 ${ruling} / 過半数 ${majority} / 定数 ${total}`, 13, C["text/primary"], "Semi Bold");
  summary.x = 18;
  summary.y = 210;
  panel.appendChild(summary);

  const status = chip("過半数到達: はい", true);
  status.x = w - 144;
  status.y = 206;
  panel.appendChild(status);
  return panel;
}

function createHeader(parent, w) {
  const header = frame("SiteHeader", 0, 0, w, 68, C["bg/surface"]);
  header.cornerRadius = 0;
  parent.appendChild(header);
  const logo = text("ウシガー", 20, C["text/primary"], "Bold");
  logo.x = 32;
  logo.y = 22;
  header.appendChild(logo);
  const nav1 = text("議員検索", 13, C["accent/cyan"], "Semi Bold");
  nav1.x = w - 196;
  nav1.y = 26;
  header.appendChild(nav1);
  const nav2 = text("このサイト", 13, C["text/secondary"], "Medium");
  nav2.x = w - 112;
  nav2.y = 26;
  header.appendChild(nav2);
}

function createCommandSearch(parent, x, y, w) {
  const panel = autoFrame("CommandSearch", x, y, w, "VERTICAL", 14, 18);
  panel.fills = solid(C["bg/command"]);
  const label = text("COMMAND SEARCH", 12, C["accent/cyan"], "Semi Bold");
  panel.appendChild(label);
  const row = figma.createFrame();
  row.name = "Search row";
  row.layoutMode = "HORIZONTAL";
  row.primaryAxisSizingMode = "AUTO";
  row.counterAxisSizingMode = "AUTO";
  row.itemSpacing = 12;
  row.fills = [];
  row.appendChild(input("氏名・よみ・政党・選挙区で検索", w - 142));
  row.appendChild(button("検索"));
  panel.appendChild(row);
  const chips = figma.createFrame();
  chips.name = "House tabs";
  chips.layoutMode = "HORIZONTAL";
  chips.primaryAxisSizingMode = "AUTO";
  chips.counterAxisSizingMode = "AUTO";
  chips.itemSpacing = 8;
  chips.fills = [];
  chips.appendChild(chip("すべて", true));
  chips.appendChild(chip("衆議院"));
  chips.appendChild(chip("参議院"));
  panel.appendChild(chips);
  parent.appendChild(panel);
  return panel;
}

function createTopPreview(page, x, y) {
  const screen = frame("Screen Preview / Top Page", x, y, 1440, 1120, C["bg/canvas"]);
  page.appendChild(screen);
  createHeader(screen, 1440);
  createCommandSearch(screen, 120, 104, 1200);
  createGauge(screen, "衆議院", 120, 286, 584, 220, 233, 465);
  createGauge(screen, "参議院", 736, 286, 584, 126, 124, 247);

  const stats = figma.createFrame();
  stats.name = "StatsCounterGrid";
  stats.x = 120;
  stats.y = 570;
  stats.layoutMode = "HORIZONTAL";
  stats.primaryAxisSizingMode = "AUTO";
  stats.counterAxisSizingMode = "AUTO";
  stats.itemSpacing = 16;
  stats.fills = [];
  stats.appendChild(stat("衆議院", "465"));
  stats.appendChild(stat("参議院", "247"));
  stats.appendChild(stat("合計", "712"));
  stats.appendChild(stat("政党・会派", "15"));
  screen.appendChild(stats);

  const filter = autoFrame("Quick Filters", 120, 700, 360, "VERTICAL", 14, 18);
  filter.appendChild(text("QUICK FILTERS", 12, C["accent/cyan"], "Semi Bold"));
  filter.appendChild(chip("院: すべて", true));
  filter.appendChild(chip("政党・会派"));
  filter.appendChild(chip("選挙区"));
  screen.appendChild(filter);

  const roster = autoFrame("Roster Preview", 512, 700, 808, "VERTICAL", 12, 18);
  roster.appendChild(text("ROSTER PREVIEW", 12, C["accent/cyan"], "Semi Bold"));
  roster.appendChild(rosterCard("逢沢 一郎", "衆議院 / 自由民主党 / 岡山1区"));
  roster.appendChild(rosterCard("青木 愛", "参議院 / 立憲民主党 / 比例"));
  screen.appendChild(roster);
}

function createSearchPreview(page, x, y) {
  const screen = frame("Screen Preview / Search Results", x, y, 1440, 940, C["bg/canvas"]);
  page.appendChild(screen);
  createHeader(screen, 1440);
  const filters = autoFrame("FilterPanel", 120, 112, 320, "VERTICAL", 16, 18);
  filters.appendChild(text("FILTER PANEL", 12, C["accent/cyan"], "Semi Bold"));
  filters.appendChild(chip("すべて", true));
  filters.appendChild(chip("衆議院"));
  filters.appendChild(chip("参議院"));
  filters.appendChild(input("政党・会派", 270));
  filters.appendChild(input("選挙区", 270));
  filters.appendChild(button("条件をクリア", "secondary"));
  screen.appendChild(filters);

  const results = autoFrame("Search Results", 472, 112, 848, "VERTICAL", 14, 18);
  results.appendChild(input("青木", 780));
  results.appendChild(text("検索: \"青木\" 2件", 14, C["text/secondary"], "Medium"));
  results.appendChild(rosterCard("青木 愛", "参議院 / 立憲民主党 / 比例"));
  results.appendChild(rosterCard("青木 一彦", "参議院 / 自由民主党 / 鳥取・島根"));
  results.appendChild(button("次へ", "secondary"));
  screen.appendChild(results);
}

function createDetailPreview(page, x, y) {
  const screen = frame("Screen Preview / Legislator Detail", x, y, 1440, 900, C["bg/canvas"]);
  page.appendChild(screen);
  createHeader(screen, 1440);
  const back = text("← 検索結果へ戻る", 14, C["text/secondary"], "Medium");
  back.x = 120;
  back.y = 102;
  screen.appendChild(back);

  const profile = autoFrame("LegislatorProfileHeader", 120, 146, 760, "VERTICAL", 12, 24);
  profile.appendChild(text("逢沢 一郎 衆議院議員", 32, C["text/primary"], "Bold"));
  profile.appendChild(text("あいさわ いちろう", 16, C["text/secondary"], "Medium"));
  const tags = figma.createFrame();
  tags.name = "Status chips";
  tags.layoutMode = "HORIZONTAL";
  tags.primaryAxisSizingMode = "AUTO";
  tags.counterAxisSizingMode = "AUTO";
  tags.itemSpacing = 8;
  tags.fills = [];
  tags.appendChild(chip("現職", true));
  tags.appendChild(chip("衆議院"));
  profile.appendChild(tags);
  screen.appendChild(profile);

  const source = autoFrame("DataSourcePanel", 912, 146, 408, "VERTICAL", 12, 20);
  source.appendChild(text("DATA SOURCE", 12, C["accent/cyan"], "Semi Bold"));
  source.appendChild(text("衆議院公式サイト", 18, C["text/primary"], "Semi Bold"));
  source.appendChild(text("最終取得日時: 2026-05-04", 13, C["text/secondary"]));
  screen.appendChild(source);

  const info = autoFrame("InfoPanel / Basic Data", 120, 386, 1200, "VERTICAL", 14, 24);
  info.appendChild(text("BASIC DATA", 12, C["accent/cyan"], "Semi Bold"));
  info.appendChild(text("所属政党・会派      自由民主党", 16, C["text/primary"], "Medium"));
  info.appendChild(text("選挙区              岡山1区", 16, C["text/primary"], "Medium"));
  info.appendChild(text("区分                小選挙区", 16, C["text/primary"], "Medium"));
  info.appendChild(text("選挙年              2024", 16, C["text/primary"], "Medium"));
  screen.appendChild(info);
}

async function createPaintStyles() {
  for (const [name, hex] of Object.entries(C)) {
    const style = figma.createPaintStyle();
    style.name = `Civic Strategy HUD/${name}`;
    style.paints = solid(hex);
  }
}

function createTokenPage(page) {
  const board = frame("Design Tokens / Color Palette", 0, 0, 1120, 900, C["bg/canvas"]);
  page.appendChild(board);
  const title = text("Civic Strategy HUD / Design Tokens", 28, C["text/primary"], "Bold");
  title.x = 40;
  title.y = 36;
  board.appendChild(title);
  let x = 40;
  let y = 104;
  let i = 0;
  for (const [name, hex] of Object.entries(C)) {
    const swatch = frame(`Token / ${name}`, x, y, 236, 96, C["bg/surface"]);
    const color = figma.createRectangle();
    color.resize(52, 52);
    color.x = 14;
    color.y = 22;
    color.cornerRadius = 6;
    color.fills = solid(hex);
    color.strokes = solid(C["line/subtle"]);
    swatch.appendChild(color);
    const n = text(name, 13, C["text/primary"], "Semi Bold");
    n.x = 78;
    n.y = 24;
    swatch.appendChild(n);
    const h = text(hex, 12, C["text/secondary"]);
    h.x = 78;
    h.y = 48;
    swatch.appendChild(h);
    board.appendChild(swatch);
    x += 260;
    i += 1;
    if (i % 4 === 0) {
      x = 40;
      y += 120;
    }
  }
}

function createComponentsPage(page) {
  const board = frame("Component Library / Major Components", 0, 0, 1360, 1320, C["bg/canvas"]);
  page.appendChild(board);
  const title = text("Major Components", 28, C["text/primary"], "Bold");
  title.x = 40;
  title.y = 36;
  board.appendChild(title);
  createCommandSearch(board, 40, 104, 760);
  createGauge(board, "衆議院", 40, 312, 584, 220, 233, 465);
  const card = rosterCard("青木 愛", "参議院 / 立憲民主党 / 比例");
  card.x = 660;
  card.y = 312;
  board.appendChild(card);
  const counter = stat("合計", "712");
  counter.x = 660;
  counter.y = 500;
  board.appendChild(counter);
  const filter = autoFrame("FilterPanel", 40, 620, 360, "VERTICAL", 14, 18);
  filter.appendChild(text("FILTER PANEL", 12, C["accent/cyan"], "Semi Bold"));
  filter.appendChild(chip("すべて", true));
  filter.appendChild(input("政党・会派", 300));
  filter.appendChild(input("選挙区", 300));
  board.appendChild(filter);
}

async function main() {
  await loadFonts();
  await createPaintStyles();

  const page = figma.createPage();
  page.name = "Civic Strategy HUD";
  await figma.setCurrentPageAsync(page);

  createTokenPage(page);
  createComponentsPage(page);
  createTopPreview(page, 0, 1540);
  createSearchPreview(page, 1520, 1540);
  createDetailPreview(page, 3040, 1540);

  figma.viewport.scrollAndZoomIntoView(page.children);
  figma.closePlugin("Created Civic Strategy HUD tokens, components, and 3 screen previews.");
}

await main();
