// Figma Plugin API script for the ウシガー / Civic Strategy HUD v3 update.
// Run through the Figma connector's use_figma tool when the MCP call limit is available.

const C = {
  bg: "#070A12",
  surface: "#101622",
  raised: "#172033",
  command: "#0B1020",
  line: "#243049",
  strong: "#3D4D72",
  text: "#F2F6FF",
  sub: "#AAB8D8",
  muted: "#6F7E9E",
  cyan: "#38D5FF",
  lime: "#A7F83B",
  amber: "#FFBE3D",
  violet: "#B985FF",
  other: "#65708A",
  track: "#1E2A40"
};

function rgb(hex) {
  const v = hex.replace("#", "");
  return {
    r: parseInt(v.slice(0, 2), 16) / 255,
    g: parseInt(v.slice(2, 4), 16) / 255,
    b: parseInt(v.slice(4, 6), 16) / 255
  };
}

function fill(hex, opacity = 1) {
  return [{ type: "SOLID", color: rgb(hex), opacity }];
}

async function loadFonts() {
  for (const style of ["Regular", "Medium", "Semi Bold", "Bold"]) {
    await figma.loadFontAsync({ family: "Inter", style });
  }
}

function text(value, x, y, size = 14, color = C.text, weight = "Regular") {
  const node = figma.createText();
  node.fontName = { family: "Inter", style: weight };
  node.fontSize = size;
  node.characters = value;
  node.fills = fill(color);
  node.x = x;
  node.y = y;
  node.lineHeight = { unit: "PERCENT", value: 130 };
  return node;
}

function frame(name, x, y, w, h, bg = C.surface) {
  const node = figma.createFrame();
  node.name = name;
  node.x = x;
  node.y = y;
  node.resize(w, h);
  node.fills = fill(bg);
  node.strokes = fill(C.line);
  node.strokeWeight = 1;
  node.cornerRadius = 2;
  node.clipsContent = false;
  return node;
}

function panel(parent, name, x, y, w, h, title) {
  const node = frame(name, x, y, w, h);
  parent.appendChild(node);
  node.appendChild(text(title, 18, 16, 12, C.cyan, "Bold"));
  return node;
}

function input(label, x, y, w) {
  const node = frame("Input", x, y, w, 42, C.bg);
  node.strokes = fill(C.strong);
  node.cornerRadius = 4;
  node.appendChild(text(label, 14, 12, 13, C.muted));
  return node;
}

function chip(label, x, y, active = false) {
  const node = frame(`Chip / ${label}`, x, y, 72, 30, active ? "#102B3A" : C.raised);
  node.cornerRadius = 999;
  node.strokes = fill(active ? C.cyan : C.line);
  node.appendChild(text(label, 12, 8, 12, active ? C.text : C.sub, "Medium"));
  return node;
}

function arcPath(cx, cy, r, startAngle, endAngle) {
  const point = (angle) => ({
    x: cx + r * Math.cos((Math.PI * angle) / 180),
    y: cy + r * Math.sin((Math.PI * angle) / 180)
  });
  const start = point(startAngle);
  const end = point(endAngle);
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${endAngle - startAngle <= 180 ? 0 : 1} 1 ${end.x} ${end.y}`;
}

function gauge(parent, title, x, y, total, ruling, segments) {
  const node = panel(parent, `PowerSemicircleGauge / ${title}`, x, y, 566, 286, `${title} 勢力図`);
  node.appendChild(text("左から: 与党第1党 → 与党第2党 → 野党第1党...", 18, 42, 11, C.muted));

  let cursor = 180;
  const track = figma.createNodeFromSvg(
    `<svg width="260" height="150" viewBox="0 0 260 150" xmlns="http://www.w3.org/2000/svg"><path d="${arcPath(130, 122, 92, 180, 360)}" fill="none" stroke="${C.track}" stroke-width="18" stroke-linecap="round"/><line x1="130" y1="18" x2="130" y2="116" stroke="white" stroke-width="2"/></svg>`
  );
  track.x = 148;
  track.y = 64;
  node.appendChild(track);

  for (const segment of segments) {
    const end = cursor + (segment.seats / total) * 180;
    const arc = figma.createNodeFromSvg(
      `<svg width="260" height="150" viewBox="0 0 260 150" xmlns="http://www.w3.org/2000/svg"><path d="${arcPath(130, 122, 92, cursor, end)}" fill="none" stroke="${segment.color}" stroke-width="18" stroke-linecap="round"/></svg>`
    );
    arc.x = 148;
    arc.y = 64;
    node.appendChild(arc);
    cursor = end;
  }

  const majority = Math.floor(total / 2) + 1;
  node.appendChild(text(`与党 ${ruling} / 現員 ${total}`, 18, 222, 13, C.text, "Bold"));
  node.appendChild(text(`過半数ライン ${majority}`, 164, 222, 13, C.sub));
  node.appendChild(text(ruling >= majority ? "過半数到達: はい" : "過半数到達: いいえ", 304, 222, 12, ruling >= majority ? C.lime : C.amber, "Bold"));

  segments.slice(0, 5).forEach((segment, index) => {
    const dot = frame("Legend dot", 18 + index * 100, 250, 10, 10, segment.color);
    dot.cornerRadius = 999;
    node.appendChild(dot);
    node.appendChild(text(`${segment.role} ${segment.short} ${segment.seats}`, 34 + index * 100, 246, 10, C.sub));
  });
}

async function main() {
  await loadFonts();
  const page = figma.createPage();
  page.name = "Civic Strategy HUD v3";
  await figma.setCurrentPageAsync(page);

  const screen = frame("Screen Preview / Top Page v3", 0, 0, 1440, 1080, C.bg);
  page.appendChild(screen);

  const header = frame("SiteHeader / ウシガー", 0, 0, 1440, 56, C.surface);
  screen.appendChild(header);
  header.appendChild(text("ウシガー", 32, 17, 20, C.text, "Bold"));
  header.appendChild(text("議員検索", 1220, 20, 13, C.cyan, "Bold"));
  header.appendChild(text("このサイト", 1300, 20, 13, C.sub));

  const search = panel(screen, "SearchPanel / 政治家を探す", 120, 96, 760, 178, "政治家を探す");
  search.appendChild(input("氏名・よみ・政党・選挙区で検索", 24, 58, 560));
  const searchButton = frame("Search Button", 604, 58, 112, 42, C.cyan);
  searchButton.appendChild(text("検索", 40, 12, 14, C.bg, "Bold"));
  search.appendChild(searchButton);
  search.appendChild(chip("すべて", 24, 118, true));
  search.appendChild(chip("衆議院", 104, 118));
  search.appendChild(chip("参議院", 184, 118));

  const quick = panel(screen, "QuickSearchPanel / クイック検索", 904, 96, 416, 178, "クイック検索");
  quick.appendChild(text("院", 18, 52, 12, C.sub, "Bold"));
  quick.appendChild(chip("すべて", 52, 44, true));
  quick.appendChild(chip("衆議院", 132, 44));
  quick.appendChild(chip("参議院", 212, 44));
  quick.appendChild(input("政党・会派", 18, 88, 180));
  quick.appendChild(input("選挙区", 210, 88, 180));

  gauge(screen, "衆議院", 120, 314, 465, 352, [
    { role: "与党1", short: "自民", seats: 316, color: C.cyan },
    { role: "与党2", short: "維新", seats: 36, color: C.lime },
    { role: "野党1", short: "中道", seats: 48, color: C.amber },
    { role: "野党2", short: "国民", seats: 28, color: C.violet },
    { role: "その他", short: "他", seats: 37, color: C.other }
  ]);

  gauge(screen, "参議院", 754, 314, 247, 120, [
    { role: "与党1", short: "自民", seats: 101, color: C.cyan },
    { role: "与党2", short: "維新", seats: 19, color: C.lime },
    { role: "野党1", short: "立憲", seats: 40, color: C.amber },
    { role: "野党2", short: "国民", seats: 25, color: C.violet },
    { role: "その他", short: "他", seats: 62, color: C.other }
  ]);

  const fresh = panel(screen, "FeaturedFreshmenPanel / 注目の大型新人議員", 120, 758, 1200, 220, "注目の大型新人議員");
  fresh.appendChild(text("当選1期目の判定データ追加後、話題性・代表性・新規性の事実に基づいて自動抽出します。", 18, 48, 13, C.sub));
  ["候補A", "候補B", "候補C"].forEach((name, index) => {
    const card = frame(`FreshmanCard / ${name}`, 18 + index * 388, 86, 366, 104, C.raised);
    card.appendChild(text(name, 14, 14, 18, C.text, "Bold"));
    card.appendChild(text("衆/参 ・ 政党・会派 ・ 選挙区", 14, 42, 12, C.sub));
    card.appendChild(text("当選回数データ追加後に注目理由を表示", 14, 70, 11, C.amber, "Bold"));
    fresh.appendChild(card);
  });

  figma.viewport.scrollAndZoomIntoView([screen]);
  figma.closePlugin("Created Civic Strategy HUD v3 page.");
}

await main();
