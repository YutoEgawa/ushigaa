const configuredApiBase = window.USHIGA_API_BASE || "";
const isLocalFrontend = ["127.0.0.1", "localhost"].includes(window.location.hostname);
const API_BASE =
  isLocalFrontend && configuredApiBase.includes("api.ushigaa.com")
    ? "http://127.0.0.1:8000/v1"
    : configuredApiBase || "http://127.0.0.1:8000/v1";
const BRAND_NAME = "ウシガー";
const QUESTION_PAGE_SIZE = 50;

const fallbackLegislators = [
  {
    id: "2b3fc98c-0c82-4f95-a150-b9a67945c629",
    name_kanji: "赤松 健",
    name_kana: "あかまつ けん",
    house: "sangiin",
    party_name: "自由民主党",
    party_short: "自民",
    district_name: "比例",
    district_type: "比例代表",
    election_year: 2022
  },
  {
    id: "sample-aisawa",
    name_kanji: "逢沢 一郎",
    name_kana: "あいさわ いちろう",
    house: "shugiin",
    party_name: "自由民主党",
    party_short: "自民",
    district_name: "岡山1区",
    district_type: "小選挙区",
    election_year: 2024
  },
  {
    id: "sample-aoki-ai",
    name_kanji: "青木 愛",
    name_kana: "あおき あい",
    house: "sangiin",
    party_name: "立憲民主党",
    party_short: "立憲",
    district_name: "比例",
    district_type: "比例代表",
    election_year: 2025
  },
  {
    id: "sample-aoki-kazuhiko",
    name_kanji: "青木 一彦",
    name_kana: "あおき かずひこ",
    house: "sangiin",
    party_name: "自由民主党",
    party_short: "自民",
    district_name: "鳥取・島根",
    district_type: "選挙区",
    election_year: 2025
  }
];

const gaugeColors = ["#38D5FF", "#A7F83B", "#FFBE3D", "#B985FF", "#FF6B45", "#35E0A1", "#6F8CFF"];
const ageMinOptions = [25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80];
const ageMaxOptions = [29, 34, 39, 44, 49, 54, 59, 64, 69, 74, 79, 84];
const electionCountOptions = Array.from({ length: 15 }, (_, index) => index + 1);
const questionCountOptions = [0, 1, 2, 3, 5, 10, 20, 30, 50, 75, 100];
const fallbackParties = [
  { id: "party-ldp", name: "自由民主党", name_short: "自民", alignment: "ruling", alignment_rank: 1 },
  { id: "party-ishin", name: "日本維新の会", name_short: "維新", alignment: "ruling", alignment_rank: 2 },
  { id: "party-cdp", name: "立憲民主党", name_short: "立憲", alignment: "opposition", alignment_rank: 1 },
  { id: "party-komei", name: "公明党", name_short: "公明", alignment: "opposition", alignment_rank: 2 }
];
const fallbackDistricts = [
  { id: "district-okayama-1", name: "岡山1区", house: "shugiin" },
  { id: "district-proportional", name: "比例", house: "sangiin" },
  { id: "district-tottori-shimane", name: "鳥取・島根", house: "sangiin" }
];
const fallbackQuestions = [
  {
    date: "2025-11-20",
    name_of_meeting: "文教科学委員会",
    name_of_house: "参議院",
    speaker: "赤松健",
    speech_count: 3,
    speech:
      "○赤松健君 おはようございます。全国比例、赤松健でございます。質問の機会をありがとうございます。では、早速始めたいと思います。大臣の所信で、デジタル教科書の活用を進めるという御発言がございました。そこで、まずこのデジタル教科書に関してお伺いします。現状は、紙の教科書と全てが同内容のいわゆるデジタル化した教科書、これを代替教材として教育課程の一部において使用することが認められておりますが、デジタル教科書の今後の推進策に関して概要を教えてください。\n\n○赤松健君 ありがとうございます。十一月十八日に、読売新聞のアンケート調査なんですけれども、九十市区の教育委員会の六割がこのデジタル教科書で視力の低下とか使用の際の通信障害などを心配しているという記事があったんですけれども、もしこのような懸念とか心配があるとすればどのように対処していくのか、教えてください。\n\n○赤松健君 ありがとうございます。デジタル教科書の現在の、今現在の活用状況について教えてください。",
    source_issue_ids: ["sample-issue"],
    source_speech_ids: ["sample-speech-1", "sample-speech-2", "sample-speech-3"]
  }
];

let state = readState();
let apiOffline = false;
const root = document.querySelector("#root");

window.addEventListener("popstate", () => {
  state = readState();
  render();
});

render();

function readState() {
  const params = new URLSearchParams(window.location.search);
  const view = params.get("view") || "top";
  return {
    view,
    q: params.get("q") || "",
    house: params.get("house") || "all",
    party: params.get("party") || "",
    district: params.get("district") || "",
    parties: readListParam(params, "parties", params.get("party")),
    districts: readListParam(params, "districts", params.get("district")),
    ageMin: params.get("age_min") || "",
    ageMax: params.get("age_max") || "",
    electionMin: params.get("election_min") || "",
    electionMax: params.get("election_max") || "",
    questionMin: params.get("question_min") || "",
    questionMax: params.get("question_max") || "",
    governmentRole: params.get("government_role") || "all",
    proportional: params.get("proportional") || "all",
    id: params.get("id") || ""
  };
}

function navigate(next) {
  const params = new URLSearchParams();
  if (next.view && next.view !== "top") params.set("view", next.view);
  if (next.q) params.set("q", next.q);
  if (next.house && next.house !== "all") params.set("house", next.house);
  setListParam(params, "parties", next.parties ?? (next.party ? [next.party] : []));
  setListParam(params, "districts", next.districts ?? (next.district ? [next.district] : []));
  if (next.ageMin) params.set("age_min", next.ageMin);
  if (next.ageMax) params.set("age_max", next.ageMax);
  if (next.electionMin) params.set("election_min", next.electionMin);
  if (next.electionMax) params.set("election_max", next.electionMax);
  if (next.questionMin) params.set("question_min", next.questionMin);
  if (next.questionMax) params.set("question_max", next.questionMax);
  if (next.governmentRole && next.governmentRole !== "all") params.set("government_role", next.governmentRole);
  if (next.proportional && next.proportional !== "all") params.set("proportional", next.proportional);
  if (next.id) params.set("id", next.id);
  const query = params.toString();
  history.pushState(null, "", query ? `?${query}` : location.pathname);
  state = readState();
  render();
}

function readListParam(params, key, fallback = "") {
  const value = params.get(key) || fallback || "";
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function setListParam(params, key, values) {
  const uniqueValues = [...new Set((values || []).filter(Boolean))];
  if (uniqueValues.length) params.set(key, uniqueValues.join(","));
}

async function api(path, fallback) {
  try {
    const response = await fetch(`${API_BASE}${path}`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    apiOffline = false;
    return await response.json();
  } catch {
    apiOffline = true;
    return fallback;
  }
}

async function listLegislators({
  q = "",
  house = "all",
  party = "",
  district = "",
  questionMin = "",
  questionMax = "",
  governmentRole = "all",
  limit = 24,
  offset = 0
} = {}) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
  if (q) params.set("q", q);
  if (house !== "all") params.set("house", house);
  if (party) params.set("party", party);
  if (district) params.set("district", district);
  if (questionMin !== "") params.set("question_count_min", questionMin);
  if (questionMax !== "") params.set("question_count_max", questionMax);
  if (governmentRole !== "all") params.set("government_role", governmentRole);
  const fallbackItems = fallbackLegislators.filter((item) => {
    const matchesHouse = house === "all" || item.house === house;
    const matchesParty = !party || item.party_name === party;
    const matchesDistrict = !district || item.district_name === district;
    const matchesGovernmentRole = matchesGovernmentRoleFilter(item, governmentRole);
    const matchesQuery =
      !q ||
      item.name_kanji.includes(q) ||
      item.name_kana.includes(q) ||
      item.party_name.includes(q) ||
      item.district_name.includes(q);
    return matchesHouse && matchesParty && matchesDistrict && matchesGovernmentRole && matchesQuery;
  });
  return api(`/legislators?${params}`, {
    items: fallbackItems,
    count: fallbackItems.length,
    limit,
    offset: 0
  });
}

async function listFilteredLegislators({
  q = "",
  house = "all",
  parties = [],
  districts = [],
  ageMin = "",
  ageMax = "",
  electionMin = "",
  electionMax = "",
  questionMin = "",
  questionMax = "",
  governmentRole = "all",
  proportional = "all"
} = {}) {
  const hasAdvancedFilters =
    parties.length ||
    districts.length ||
    ageMin ||
    ageMax ||
    electionMin ||
    electionMax ||
    questionMin !== "" ||
    questionMax !== "" ||
    governmentRole !== "all" ||
    proportional !== "all";
  if (!hasAdvancedFilters) {
    return listLegislators({ q, house, limit: 50, offset: 0 });
  }
  if (
    parties.length <= 1 &&
    districts.length <= 1 &&
    !ageMin &&
    !ageMax &&
    !electionMin &&
    !electionMax &&
    questionMin === "" &&
    questionMax === "" &&
    governmentRole === "all" &&
    proportional === "all"
  ) {
    return listLegislators({ q, house, party: parties[0] || "", district: districts[0] || "", limit: 50, offset: 0 });
  }
  const firstPage = await listLegislators({ q, house, questionMin, questionMax, governmentRole, limit: 100, offset: 0 });
  let items = [...firstPage.items];
  const total = firstPage.count ?? firstPage.items.length;
  for (let offset = firstPage.items.length; offset < total; offset += 100) {
    const page = await listLegislators({ q, house, questionMin, questionMax, governmentRole, limit: 100, offset });
    items = items.concat(page.items);
    if (!page.items.length) break;
  }
  const filteredItems = items
    .filter((item) => matchesAdvancedFilters(item, { parties, districts, ageMin, ageMax, electionMin, electionMax, proportional }));
  return {
    items: filteredItems,
    count: filteredItems.length,
    limit: filteredItems.length,
    offset: 0
  };
}

async function getLegislator(id) {
  return api(`/legislators/${id}`, fallbackLegislators.find((item) => item.id === id) || fallbackLegislators[0]);
}

async function listLegislatorQuestions(id, { limit = QUESTION_PAGE_SIZE, offset = 0 } = {}) {
  const fallbackIds = new Set(["sample-akama-ken", "2b3fc98c-0c82-4f95-a150-b9a67945c629"]);
  const fallback = fallbackIds.has(id)
    ? await getAkamatsuQuestionFixture({ limit, offset })
    : { items: [], count: 0, from_date: "2023-01-01" };
  return api(`/legislators/${id}/questions?from=2023-01-01&limit=${limit}&offset=${offset}`, fallback);
}

async function listLegislatorQuestionTopicRankings(id) {
  return api(`/legislators/${id}/question-topic-rankings?from=2023-01-01`, {
    items: [],
    from_date: "2023-01-01",
    unit: "question_group"
  });
}

async function listQuestionTopicTopRankings() {
  return api("/kokkai/question-topic-rankings?from=2023-01-01&limit=10", {
    items: [],
    from_date: "2023-01-01",
    unit: "question_group"
  });
}

async function getAkamatsuQuestionFixture({ limit = QUESTION_PAGE_SIZE, offset = 0 } = {}) {
  try {
    const response = await fetch("./data/kokkai_questions_akamatsu.json");
    if (response.ok) return sliceQuestionFixture(await response.json(), limit, offset);
  } catch {
    // Fall through to the tiny inline fixture when local static data is unavailable.
  }
  return sliceQuestionFixture({ items: fallbackQuestions, count: fallbackQuestions.length, from_date: "2023-01-01" }, limit, offset);
}

function sliceQuestionFixture(data, limit, offset) {
  const items = data.items || [];
  return {
    ...data,
    items: items.slice(offset, offset + limit),
    count: data.count ?? items.length
  };
}

async function listParties(house = "all") {
  const path = house === "all" ? "/parties" : `/parties?house=${house}`;
  return api(path, fallbackParties);
}

async function listDistricts(house = "all") {
  const path = house === "all" ? "/districts" : `/districts?house=${house}`;
  return api(path, fallbackDistricts.filter((item) => house === "all" || item.house === house));
}

function fallbackPowerMap() {
  return {
    shugiin: buildGaugeData("衆議院", fallbackLegislators.filter((item) => item.house === "shugiin"), fallbackParties),
    sangiin: buildGaugeData("参議院", fallbackLegislators.filter((item) => item.house === "sangiin"), fallbackParties)
  };
}

async function getPowerMap() {
  return api("/power-map", null);
}

async function listFeaturedFreshmen(limit = 3) {
  return api(`/featured-freshmen?limit=${limit}`, []);
}

async function listAllLegislatorsByHouse(house) {
  const items = [];
  let offset = 0;
  const limit = 100;
  while (true) {
    const data = await listLegislators({ house, limit, offset });
    items.push(...data.items);
    if (data.items.length < limit) break;
    offset += limit;
  }
  return items;
}

async function render() {
  root.innerHTML = `
    <div class="app-shell">
      ${siteHeader()}
      <main class="page-frame" id="page"></main>
      ${siteFooter()}
    </div>
  `;
  bindHeader();
  if (state.view === "search") await renderSearch();
  else if (state.view === "detail" && state.id) await renderDetail();
  else if (state.view === "activity") await renderActivity();
  else if (state.view === "about") renderAbout();
  else if (state.view === "contact") renderContact();
  else if (state.view === "terms") renderTerms();
  else if (state.view === "privacy") renderPrivacy();
  else await renderTop();
}

function siteHeader() {
  return `
    <header class="site-header">
      <button class="brand-button" data-nav="top">${BRAND_NAME}</button>
      <nav class="site-nav" aria-label="Primary navigation">
        <button class="nav-link ${state.view === "top" || state.view === "search" || state.view === "detail" ? "is-active" : ""}" data-nav="top">議員検索</button>
        <button class="nav-link ${state.view === "activity" ? "is-active" : ""}" data-nav="activity">国会での活動</button>
        <button class="nav-link ${state.view === "about" ? "is-active" : ""}" data-nav="about">ウシガーについて</button>
        <button class="nav-link ${state.view === "contact" ? "is-active" : ""}" data-nav="contact">問い合わせ</button>
      </nav>
      <button class="menu-button" aria-label="メニュー">☰</button>
    </header>
  `;
}

function siteFooter() {
  return `
    <footer class="site-footer">
      <div>
        <strong>${BRAND_NAME}</strong>
        <span>公開情報を整理する国会議員データベース</span>
      </div>
      <nav aria-label="Footer navigation">
        <button class="footer-link" data-nav="terms">利用規約</button>
        <button class="footer-link" data-nav="privacy">プライバシーポリシー</button>
      </nav>
    </footer>
  `;
}

function bindHeader() {
  document.querySelectorAll("[data-nav]").forEach((button) => {
    button.addEventListener("click", () => navigate({ view: button.dataset.nav }));
  });
}

async function renderTop() {
  const page = document.querySelector("#page");
  renderTopContent({
    page,
    parties: fallbackParties,
    districts: fallbackDistricts,
    powerMap: null,
    featuredFreshmen: null,
    isLoading: true
  });

  const [parties, districts, powerMap, featuredFreshmen] = await Promise.all([
    listParties(),
    listDistricts(state.house),
    getPowerMap(),
    listFeaturedFreshmen(3)
  ]);
  if (state.view !== "top") return;
  renderTopContent({ page, parties, districts, powerMap, featuredFreshmen });
}

function renderTopContent({ page, parties, districts, powerMap, featuredFreshmen, isLoading = false }) {
  page.className = "page-frame top-page";
  page.innerHTML = `
    ${topPageTabs("search")}
    ${fallbackBanner()}
    <section class="top-control-row">
      ${commandSearch("", { house: "all", parties: [], districts: [], ageMin: "", ageMax: "", electionMin: "", electionMax: "", questionMin: "", questionMax: "", governmentRole: "all", proportional: "all" }, parties, districts)}
      ${quickSearchPanel()}
    </section>
    <section class="power-map-strip" aria-label="勢力図">
      ${powerMap ? `${gauge(powerMap.shugiin)}${gauge(powerMap.sangiin)}` : powerMapLoadingPanels(isLoading)}
    </section>
    <section class="hud-panel featured-freshmen-panel">
      <div class="panel-title">注目の大型新人議員</div>
      <p class="panel-note">${isLoading ? "最新データを読み込み中です。" : "当選1回目の議員からランダムに表示しています。"}</p>
      <div class="featured-grid">
        ${featuredFreshmen === null ? loadingCards("大型新人議員を読み込み中です。") : featuredFreshmenCards(featuredFreshmen)}
      </div>
    </section>
    <section class="hud-panel top-intro-panel" aria-label="ウシガーの説明">
      <div>
        <p class="panel-title">WHAT IS USHIGAA?</p>
        <p>ウシガーは、国会議員のプロフィール、所属、選挙区、経歴、政治勢力図を公開情報からまとめて検索できる政治家データベースです。</p>
      </div>
      <button class="secondary-button" id="top-about-link" type="button">ウシガーについて</button>
    </section>
  `;
  bindCommandSearch();
  bindTopPageTabs();
  bindOpenDetails();
  bindQuickSearch();
  bindTopIntro();
}

async function renderActivity() {
  const page = document.querySelector("#page");
  renderActivityContent(page, null, true);
  const rankings = await listQuestionTopicTopRankings();
  if (state.view !== "activity") return;
  renderActivityContent(page, rankings);
}

function renderActivityContent(page, rankings, isLoading = false) {
  page.className = "page-frame activity-page";
  page.innerHTML = `
    ${topPageTabs("activity")}
    ${fallbackBanner()}
    <section class="activity-hero">
      <p class="panel-title">KOKKAI ACTIVITY</p>
      <h1>国会での活動</h1>
      <p>2023年以降の国会質疑について、委員会ごとに発言量の多い政治家を表示しています。</p>
    </section>
    <section class="activity-ranking-grid">
      ${activityRankingList(rankings, isLoading)}
    </section>
  `;
  bindTopPageTabs();
  bindOpenDetails();
}

function topPageTabs(active) {
  return `
    <nav class="top-page-tabs" aria-label="トップページの表示切替">
      <button class="top-page-tab ${active === "search" ? "is-active" : ""}" type="button" data-nav="top">議員検索</button>
      <button class="top-page-tab ${active === "activity" ? "is-active" : ""}" type="button" data-nav="activity">国会での活動</button>
    </nav>
  `;
}

function bindTopPageTabs() {
  document.querySelectorAll(".top-page-tab[data-nav]").forEach((button) => {
    button.addEventListener("click", () => navigate({ view: button.dataset.nav }));
  });
}

function activityRankingList(rankings, isLoading) {
  if (isLoading) return loadingCards("委員会ごとのランキングを読み込み中です。");
  const items = rankings?.items || [];
  if (!items.length) return `<div class="empty-state">ランキングデータを読み込めませんでした。</div>`;
  return items.map(activityTopicRankingCard).join("");
}

function activityTopicRankingCard(topic) {
  return `
    <article class="hud-panel activity-ranking-card">
      <div class="activity-ranking-head">
        <div>
          <p class="panel-title">${topic.total_legislators}人が質疑</p>
          <h2>${escapeHtml(topic.topic)}</h2>
        </div>
      </div>
      <ol class="activity-ranking-list">
        ${(topic.items || []).map(activityRankingRow).join("")}
      </ol>
    </article>
  `;
}

function activityRankingRow(item) {
  return `
    <li>
      <span>${item.rank}位</span>
      <button class="activity-ranking-name" type="button" data-open="${escapeHtml(item.legislator_id)}">${escapeHtml(item.name_kanji)}</button>
      <span>${escapeHtml(item.party_name || "")}</span>
      <strong>${item.question_count}回</strong>
    </li>
  `;
}

function powerMapLoadingPanels(isLoading) {
  const message = isLoading ? "勢力図を読み込み中です。" : "勢力図を読み込めませんでした。";
  return `
    <section class="hud-panel gauge-panel">
      <div class="panel-title">衆議院 勢力図</div>
      <div class="loading-state">${message}</div>
    </section>
    <section class="hud-panel gauge-panel">
      <div class="panel-title">参議院 勢力図</div>
      <div class="loading-state">${message}</div>
    </section>
  `;
}

function loadingCards(message) {
  return `<div class="empty-state">${escapeHtml(message)}</div>`;
}

async function renderSearch() {
  const page = document.querySelector("#page");
  renderSearchContent({
    page,
    data: null,
    parties: fallbackParties,
    districts: fallbackDistricts.filter((item) => state.house === "all" || item.house === state.house),
    isLoading: true
  });

  const [data, parties, districts] = await Promise.all([
    listFilteredLegislators({
      q: state.q,
      house: state.house,
      parties: state.parties,
      districts: state.districts,
      ageMin: state.ageMin,
      ageMax: state.ageMax,
      electionMin: state.electionMin,
      electionMax: state.electionMax,
      questionMin: state.questionMin,
      questionMax: state.questionMax,
      governmentRole: state.governmentRole,
      proportional: state.proportional
    }),
    listParties(),
    listDistricts(state.house)
  ]);
  if (state.view !== "search") return;
  renderSearchContent({ page, data, parties, districts });
}

function renderSearchContent({ page, data, parties, districts, isLoading = false }) {
  page.className = "page-frame search-page";
  page.innerHTML = `
    <section class="hud-panel filter-panel search-filter-panel">
      <div class="panel-title">政治家を探す</div>
      ${searchFilterControls("result", state, parties, districts)}
      <button class="primary-button" data-apply-filters>この条件で検索</button>
      <button class="secondary-button" data-clear>条件をクリア</button>
    </section>
    <section class="hud-panel search-results">
      <div class="search-results-head">
        <input value="${escapeHtml(state.q)}" aria-label="検索キーワード" id="result-search" />
        <span>${searchResultStatus(data, isLoading)}</span>
      </div>
      <div class="results-list">
        ${isLoading ? searchLoadingState() : searchResultList(data)}
      </div>
    </section>
  `;
  document.querySelector("#result-search").addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      navigate({ view: "search", q: event.target.value, ...collectSearchFilters(document.querySelector(".search-filter-panel")) });
    }
  });
  bindSearchFilterChips(".search-filter-panel");
  document.querySelector("[data-apply-filters]").addEventListener("click", () => {
    navigate({ view: "search", q: document.querySelector("#result-search").value, ...collectSearchFilters(document.querySelector(".search-filter-panel")) });
  });
  document.querySelector("[data-clear]").addEventListener("click", () => navigate({ view: "search", q: state.q, house: "all" }));
  bindOpenDetails();
}

function searchResultStatus(data, isLoading) {
  if (isLoading) return "検索中 / データリンク確立中";
  return `${state.q ? `検索: "${escapeHtml(state.q)}"` : "すべての議員"} / ${data.count ?? data.items.length}件`;
}

function searchResultList(data) {
  return data.items.length
    ? data.items.map(rosterCard).join("")
    : `<div class="empty-state">条件に一致する議員が見つかりませんでした。</div>`;
}

function searchLoadingState() {
  return `
    <section class="search-loading" role="status" aria-live="polite">
      <div class="scan-core" aria-hidden="true"><span></span><i></i></div>
      <div class="scan-copy">
        <p class="panel-title">SEARCHING DATABASE</p>
        <h2>政治家データをスキャン中</h2>
        <p>条件に一致する議員を照合しています。</p>
      </div>
      <div class="scan-bars" aria-hidden="true">
        <span></span><span></span><span></span><span></span><span></span>
      </div>
    </section>
  `;
}

async function renderDetail() {
  const [item, questions, topicRankings] = await Promise.all([
    getLegislator(state.id),
    listLegislatorQuestions(state.id),
    listLegislatorQuestionTopicRankings(state.id)
  ]);
  const page = document.querySelector("#page");
  const profileSource = item.profile_source_url || item.birth_date_source_url || item.election_count_source_url || item.career_source_url;
  page.className = "page-frame detail-page";
  page.innerHTML = `
    <button class="back-link" data-back>← 検索結果へ戻る</button>
    <section class="detail-hero">
      <section class="hud-panel profile-header">
        <h1>${escapeHtml(item.name_kanji)} ${houseLabel(item.house)}議員</h1>
        <p>${escapeHtml(item.name_kana)}</p>
        <div class="segmented-control">
          <span class="chip is-active">現職</span>
          <span class="chip">${houseLabel(item.house)}</span>
        </div>
      </section>
      <section class="hud-panel source-panel">
        <div class="panel-title">DATA SOURCE</div>
        <h2>${sourceLabel(item.profile_source_type, item.house)}</h2>
        <p>最終確認日: ${escapeHtml(item.profile_source_checked_at || "未取得")}</p>
        ${profileSource ? `<a class="text-button" href="${escapeHtml(profileSource)}" target="_blank" rel="noreferrer">出典を開く</a>` : ""}
      </section>
    </section>
    <section class="hud-panel basic-data">
      <div class="panel-title">BASIC DATA</div>
      <dl>
        ${dataRow("所属政党・会派", item.party_name || "未設定")}
        ${dataRow("選挙区", item.district_name || "未設定")}
        ${dataRow("区分", districtTypeLabel(item.district_type))}
        ${dataRow("当選年", item.election_year || "未設定")}
        ${dataRow("当選回数", formatElectionCount(item))}
        ${dataRow("生年月日", formatBirthDate(item))}
        ${dataRow("年齢", calculateAge(item))}
      </dl>
      <p class="detail-meta">${metaLine(item)}</p>
    </section>
    <section class="hud-panel career-data">
      <div class="panel-title">CAREER LOG</div>
      <p>${escapeHtml(item.career_summary || "公式プロフィールから経歴を取得でき次第、ここに表示します。")}</p>
    </section>
    <section class="hud-panel topic-ranking-data">
      <div class="question-header">
        <div>
          <div class="panel-title">COMMITTEE CONTRIBUTION</div>
          <h2>議論に貢献している委員会</h2>
        </div>
        <span>2023年以降</span>
      </div>
      ${topicRankingList(topicRankings)}
    </section>
    <section class="hud-panel question-data">
      <div class="question-header">
        <div>
          <div class="panel-title">KOKKAI QUESTIONS</div>
          <h2>2023年以降の質疑</h2>
        </div>
        <span data-question-count>${questionCountLabel(questions.items.length, questions.count)}</span>
      </div>
      ${questionList(questions)}
    </section>
  `;
  document.querySelector("[data-back]").addEventListener("click", () => history.back());
  bindOpenDetails();
  bindQuestionLoadMore(state.id);
}

function topicRankingList(data) {
  const items = (data.items || []).filter((item) => Number(item.current_rank) <= 10);
  if (!items.length) {
    return `<div class="empty-state">2023年以降、上位10位以内に入っている委員会はまだありません。</div>`;
  }
  return `
    <div class="topic-ranking-list">
      ${items.map(topicRankingItem).join("")}
    </div>
  `;
}

function topicRankingItem(item) {
  return `
    <article class="topic-ranking-item">
      <div class="topic-ranking-summary">
        <div>
          <h3>${escapeHtml(item.topic)}</h3>
          <p>${item.total_legislators}人中 ${item.current_rank}位</p>
        </div>
        <div class="topic-ranking-score">
          <strong>${item.current_rank}位</strong>
          <span>${item.current_count}回</span>
        </div>
      </div>
    </article>
  `;
}

function questionList(data) {
  const items = data.items || [];
  if (!items?.length) {
    return `<div class="empty-state">保存済みの質疑データはまだありません。</div>`;
  }
  const hasMore = items.length < data.count;
  return `
    <div class="question-list">
      ${items.map(questionItem).join("")}
    </div>
    ${
      hasMore
        ? `<button class="secondary-button question-more-button" type="button" data-load-questions data-loaded="${items.length}" data-total="${data.count}">さらに表示</button>`
        : ""
    }
  `;
}

function questionCountLabel(loaded, total) {
  if (!total || loaded >= total) return `${total || loaded}件`;
  return `${loaded} / ${total}件`;
}

function bindQuestionLoadMore(legislatorId) {
  const button = document.querySelector("[data-load-questions]");
  if (!button) return;
  button.addEventListener("click", async () => {
    const list = document.querySelector(".question-list");
    const countLabel = document.querySelector("[data-question-count]");
    const loaded = Number(button.dataset.loaded || list?.querySelectorAll(".question-item").length || 0);
    button.disabled = true;
    button.textContent = "読み込み中";
    const next = await listLegislatorQuestions(legislatorId, { offset: loaded });
    if (!next.items.length || !list) {
      button.remove();
      return;
    }
    list.insertAdjacentHTML("beforeend", next.items.map(questionItem).join(""));
    const nextLoaded = loaded + next.items.length;
    const total = next.count ?? Number(button.dataset.total) ?? nextLoaded;
    if (countLabel) countLabel.textContent = questionCountLabel(nextLoaded, total);
    if (nextLoaded >= total) {
      button.remove();
      return;
    }
    button.dataset.loaded = String(nextLoaded);
    button.dataset.total = String(total);
    button.disabled = false;
    button.textContent = "さらに表示";
  });
}

function questionItem(item) {
  return `
    <article class="question-item">
      <div class="question-meta">
        <time datetime="${escapeHtml(item.date)}">${formatJapaneseDate(item.date)}</time>
        <span>${escapeHtml(item.name_of_meeting)}</span>
        ${item.speech_count > 1 ? `<span>${item.speech_count}発言を集約</span>` : ""}
      </div>
      <p>${escapeHtml(speechPreview(item.speech))}</p>
      <details>
        <summary>全文を開く</summary>
        <div class="question-fulltext">${speechToHtml(item.speech)}</div>
      </details>
    </article>
  `;
}

function renderAbout() {
  const page = document.querySelector("#page");
  page.className = "page-frame content-page";
  page.innerHTML = `
    <section class="content-hero">
      <p class="panel-title">ウシガーについて</p>
      <h1 class="about-main-heading">もっとオープンで、もっと刺激的な政治を、僕たちの手に。</h1>
    </section>
    <section class="content-stack">
      ${storySection("このサイトの目的", [
        "僕たちはたくさんの人と関わって生きています。家族、友達、学校の先生、会社の同僚、お客さん、数え出したらキリがありません。政治家だって同じです。自分が何者で、これまで何をしてきて、これからどこに行こうとしているのかを、応援してくれる味方や一緒に頑張っている仲間、相容れない考えを持つ相手に知ってもらうことが正しい政治活動を促していきます。",
        "「ウシガー」という本サイトでは、政治家ひとりひとりがどんな人で、どんな活動をしているのか、可能な限り中立にまとめていきたいと考えています。"
      ])}
      ${storySection("利用者に注視してほしいこと", [
        "現時点では各政治家の基礎情報をまとめた簡易的なサイトとなっています。今後は、散逸している幅広い政治活動を可視化するため、SNSでの言論活動や不祥事の有無なども追加していきます。",
        `本サイトに掲載している情報は公式サイトやSNS、他メディアの情報などの公開情報を出典としています。誤りや古い情報がございましたら、大変恐れ入りますが${navInlineLink("お問い合わせ窓口", "contact")}までご連絡をいただきますようお願い申し上げます。`
      ], { allowHtml: true })}
    </section>
  `;
}

function renderContact() {
  const page = document.querySelector("#page");
  page.className = "page-frame content-page";
  page.innerHTML = `
    <section class="content-hero">
      <p class="panel-title">ウシガーに関する問い合わせ</p>
      <h1 class="contact-main-heading">ウシガーは暇な人間が有志で運営しています。本サイトの改善に繋がるご指摘やお問い合わせにつきましては、以下のフォームをご利用の上、contact@ushigaa.comまでご連絡をいただけますと幸いです。</h1>
    </section>
    <section class="contact-section">
      <form class="contact-form">
        <label>
          <span>お名前 <strong>必須</strong></span>
          <input name="name" autocomplete="name" required />
        </label>
        <label>
          <span>ご所属 <em>任意</em></span>
          <input name="organization" autocomplete="organization" />
        </label>
        <label>
          <span>お問い合わせの種類 <strong>必須</strong></span>
          <select name="type" required>
            <option value="">選択してください</option>
            <option value="wrong-info">誤った情報のご指摘</option>
            <option value="improvement">改善のご要望</option>
            <option value="other">その他、運営へのお問い合わせ</option>
          </select>
        </label>
        <label class="contact-detail-field">
          <span>お問い合わせの詳細 <strong>必須</strong></span>
          <textarea name="detail" rows="8" required></textarea>
        </label>
        <button class="primary-button contact-submit" type="submit">メールを作成する</button>
        <p class="form-note">送信ボタンを押すと、入力内容を反映したメール作成画面が開きます。宛先: contact@ushigaa.com</p>
      </form>
    </section>
  `;
  bindContactForm();
}

function renderTerms() {
  const page = document.querySelector("#page");
  page.className = "page-frame content-page";
  page.innerHTML = `
    <section class="content-hero">
      <p class="panel-title">利用規約</p>
      <h1>利用規約</h1>
    </section>
    <section class="content-stack terms-stack">
      ${storySection("1. 本規約の適用", [
        "本規約は、ウシガー運営者が提供するウェブサイト、データベース、検索機能、問い合わせフォーム、その他これらに付随する一切のサービス（以下、「本サービス」という。）の利用に適用されます。",
        "利用者は、本サイトを利用することにより、本規約の内容に同意したものとみなされます。"
      ])}
      ${storySection("2. 本サービスの内容", [
        "本サービスは、個別の政治家、個別の政党及び各議院に関する情報を提供するサービスを含みます。",
        "運営者は、利用者への事前通知なく、本サイトの内容、表示、機能、掲載項目、データ取得方針を変更、追加、停止または終了することがあります。"
      ])}
      ${storySection("3. 掲載情報と免責", [
        "ウシガーは既に公開されている情報をもとに政治家の情報を一元化するサービスです。掲載情報の正確性、完全性、最新性を保証するものではございませんので、重要な判断や引用を行う場合は必ず衆議院、参議院、政党公式HP、本人公式HPなど、一次情報を確認してください。本サイトに掲載されている情報を利用することによって生じた損害について、運営者は責任を負いかねますのでご了承ください。"
      ])}
      ${storySection("4. 禁止事項", [
        "利用者は、本サイトの利用にあたり、法令または公序良俗に反する行為、第三者または運営者の権利を侵害する行為、本サイトの運営を妨害する行為を行ってはなりません。",
        "虚偽情報の送信、なりすまし、不正アクセス、過度なアクセス、スクレイピングその他本サイトに過度な負荷をかける行為を禁止します。",
        "本サイトの情報を、誹謗中傷、差別的表現、違法行為、選挙関連法令に違反する行為、その他不適切な目的で利用することを禁止します。"
      ])}
      ${storySection("5. 知的財産権", [
        "本サービスを通じて提供される情報（映像・音声・文章・写真・ソフトウェアを含む）は、著作権、商標権、特許権、若しくは他の知的財産権及び法律により保護されるものとします。"
      ])}
      ${storySection("6. サービスの中断・終了", [
        "運営者は、保守、障害、外部サービスの停止、セキュリティ上の必要、その他運営上または技術上の理由により、利用者に事前通知することなく本サイトの全部または一部を中断、停止または終了することがあります。",
        "本サイトの中断、停止、終了または内容変更により利用者に損害が生じた場合であっても、運営者は責任を負いかねます。"
      ])}
      ${storySection("7. 利用者の責任", [
        "利用者は、本サービスの利用によって当社若しくは第三者に損害を与えた場合又は第三者との間で紛争が生じた場合には、自己の責任と負担により解決するものとします。"
      ])}
      ${storySection("8. 本規約の変更", [
        "運営者は、利用者の承諾を要することなく、本規約に新たな規定の追加又は変更を行うことができるものとします。なお、新たに追加又は変更される規定についても本規約の一部を構成するものとします。変更後の本規約については、本サービスが別途定める場合を除いて、オンライン上に表示した時点より、効力を生じるものとします。"
      ])}
      ${storySection("9. 準拠法・管轄", [
        "本規約は日本法に準拠します。",
        "本サイトまたは本規約に関して紛争が生じた場合、東京地方裁判所を第一審の専属的合意管轄裁判所とします。"
      ])}
    </section>
  `;
}

function renderPrivacy() {
  const page = document.querySelector("#page");
  page.className = "page-frame content-page";
  page.innerHTML = `
    <section class="content-hero">
      <p class="panel-title">プライバシーポリシー</p>
      <h1>プライバシーポリシー</h1>
    </section>
    <section class="content-stack terms-stack">
      ${storySection("1. 総則", [
        "運営者は、ユーザー等情報の保護実現のため、個人情報保護法及びその他関連する法令等を遵守し、個人情報を含むユーザー等情報の適切な取扱い及び保護に努めます。",
        "運営者が提携するサービス（以下「提携サービス」といいます。）を提供する事業者（以下「提携事業者」といいます。）により提供される提携サービスその他当社以外の者が提供するサービス（以下「外部サービス」といいます。）については、本ポリシーの規定は適用されません。提携サービスにおけるユーザー等情報の取扱いについては、当該提携サービスを提供する事業者が別途定めるプライバシーポリシー等をご参照ください。"
      ])}
      ${storySection("2. 取得する情報", [
        "ウシガーは、問い合わせフォームを通じて、お名前、ご所属、ご連絡先のメールアドレス、お問い合わせの種類、お問い合わせの詳細を取得する場合があります。",
        "本サイトの改善、不正利用防止、障害調査、セキュリティ確保のため、アクセス日時、IPアドレス、ブラウザ情報、端末情報、リファラー、Cookie等の識別子、閲覧ページなどの利用情報を取得する場合があります。"
      ])}
      ${storySection("3. 利用目的", [
        "取得した個人情報は、お問い合わせへの回答、掲載情報の確認・修正、本人確認、対応履歴の管理、本サイトの改善、運営上必要な連絡のために利用します。",
        "利用情報は、本サイトの利用状況の把握、表示や機能の改善、障害対応、不正アクセスその他不正利用の防止、セキュリティ確保のために利用します。",
        "なお、運営者は、ユーザー等本人の同意なく利用目的の範囲を超えてユーザー等情報を利用することはありません。"
      ])}
      ${storySection("4. 個人情報の管理", [
        "運営者は、取得した個人情報について、漏えい、滅失、毀損、不正アクセス等を防止するため、合理的な範囲で必要な安全管理措置を講じます。",
        "お問い合わせ内容の確認が完了した後も、対応履歴の確認、不正利用防止、サービス改善のために、合理的に必要な範囲で情報を保管する場合があります。"
      ])}
      ${storySection("5. 第三者提供", [
        "運営者は、法令に基づく場合、本人の同意がある場合、人の生命、身体又は財産の保護のために必要がある場合、その他個人情報保護法上認められる場合を除き、取得した個人情報を第三者に提供しません。"
      ])}
      ${storySection("6. 取扱いの委託", [
        "運営者は、問い合わせへの対応、メール送信、データ保管、アクセス解析、サイト運営その他本サービスの提供に必要な範囲で、ユーザー等情報の取扱いの全部又は一部を提携事業者その他外部サービスを提供する事業者に委託する場合があります。"
      ])}
      ${storySection("7. 開示・訂正・利用停止等", [
        "本人から、個人情報の開示、訂正、追加、削除、利用停止、第三者提供の停止等の請求があった場合、運営者は法令に従い、合理的な範囲で対応します。",
        "請求内容によっては、本人確認に必要な情報の提示をお願いする場合があります。"
      ])}
      ${storySection("8. プライバシーポリシーの変更", [
        "運営者は、必要に応じて本プライバシーポリシーを変更することがあります。変更後の内容は、本サイト上に表示した時点から効力を生じるものとします。"
      ])}
      ${storySection("9. 問い合わせ", [
        `個人情報の取り扱いに関するお問い合わせは、${navInlineLink("問い合わせフォーム", "contact")}からご連絡ください。`
      ], { allowHtml: true })}
    </section>
  `;
}

function commandSearch(q, filters, parties, districts) {
  return `
    <section class="hud-panel command-search">
      <div class="panel-title">政治家を探す</div>
      <div class="search-row">
        <input id="command-q" value="${escapeHtml(q)}" placeholder="氏名・よみ・政党・選挙区で検索" aria-label="氏名・よみ・政党・選挙区で検索" />
        <button class="primary-button" id="command-submit">検索</button>
      </div>
      ${searchFilterControls("command", filters, parties, districts)}
    </section>
  `;
}

function bindCommandSearch() {
  const input = document.querySelector("#command-q");
  if (!input) return;
  const panel = document.querySelector(".command-search");
  const submit = () => navigate({ view: "search", q: input.value, ...collectSearchFilters(panel) });
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") submit();
  });
  document.querySelector("#command-submit").addEventListener("click", submit);
  bindSearchFilterChips(".command-search");
}

function quickSearchPanel() {
  return `
    <section class="hud-panel quick-search-panel">
      <div class="panel-title">クイック検索</div>
      <button class="secondary-button quick-action-button" type="button" data-quick-search="freshman">当選1回目の政治家を調べる</button>
      <button class="secondary-button quick-action-button" type="button" data-quick-search="under35">35歳未満の政治家を調べる</button>
      <button class="secondary-button quick-action-button" type="button" data-quick-search="multi-proportional">当選回数が複数かつ比例代表の政治家を調べる</button>
      <button class="secondary-button quick-action-button" type="button" data-quick-search="zero-questions">国会審議における活動が少ない政治家を調べる</button>
    </section>
  `;
}

function bindQuickSearch() {
  document.querySelectorAll("[data-quick-search]").forEach((button) => {
    button.addEventListener("click", () => {
      if (button.dataset.quickSearch === "freshman") {
        navigate({ view: "search", house: "all", electionMin: "1", electionMax: "1" });
        return;
      }
      if (button.dataset.quickSearch === "multi-proportional") {
        navigate({ view: "search", house: "all", electionMin: "2", proportional: "proportional" });
        return;
      }
      if (button.dataset.quickSearch === "zero-questions") {
        navigate({ view: "search", house: "all", electionMin: "2", questionMin: "0", questionMax: "0", governmentRole: "none" });
        return;
      }
      navigate({ view: "search", house: "all", ageMax: "34" });
    });
  });
}

function searchFilterControls(prefix, filters, parties, districts) {
  const selectedParties = filters.parties || [];
  const selectedDistricts = filters.districts || [];
  return `
    <div class="advanced-search-grid">
      <fieldset class="filter-group filter-group-house">
        <legend>議院</legend>
        ${segmented(filters.house || "all")}
      </fieldset>
      <fieldset class="filter-group filter-group-proportional">
        <legend>比例</legend>
        ${proportionalSegmented(filters.proportional || "all")}
      </fieldset>
      ${rangeGroup(`${prefix}-age`, "年齢", ageMinOptions, ageMaxOptions, filters.ageMin, filters.ageMax, "歳", "歳")}
      ${rangeGroup(`${prefix}-election`, "当選回数", electionCountOptions, electionCountOptions, filters.electionMin, filters.electionMax, "回", "回")}
      ${rangeGroup(`${prefix}-question`, "国会審議における近年の質疑回数", questionCountOptions, questionCountOptions, filters.questionMin, filters.questionMax, "回", "回")}
      <fieldset class="filter-group">
        <legend>2023年以降の政府役職</legend>
        ${governmentRoleSegmented(filters.governmentRole || "all")}
      </fieldset>
      ${suggestionGroup(`${prefix}-party`, "政党", parties.map((item) => item.name), selectedParties, "政党名を入力")}
      ${suggestionGroup(`${prefix}-district`, "選挙区", districts.map((item) => item.name), selectedDistricts, "選挙区を入力")}
    </div>
  `;
}

function suggestionGroup(name, label, values, selectedValues, placeholder) {
  const uniqueValues = [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b, "ja"));
  return `
    <fieldset class="filter-group filter-group-wide" data-suggest-group="${escapeHtml(name)}">
      <legend>${escapeHtml(label)}</legend>
      <div class="suggest-row">
        <input type="text" list="${escapeHtml(name)}-options" data-suggest-input="${escapeHtml(name)}" placeholder="${escapeHtml(placeholder)}" />
        <button class="secondary-button" type="button" data-add-suggestion="${escapeHtml(name)}">追加</button>
        <datalist id="${escapeHtml(name)}-options">
          ${uniqueValues.map((value) => `<option value="${escapeHtml(value)}"></option>`).join("")}
        </datalist>
      </div>
      <div class="selected-token-list" data-selected-tokens="${escapeHtml(name)}">
        ${(selectedValues || [])
          .map((value) => `
            <button class="selected-token" type="button" data-token-value="${escapeHtml(value)}" aria-label="${escapeHtml(value)}を削除">
              ${escapeHtml(value)} <span>×</span>
            </button>
          `)
          .join("")}
      </div>
    </fieldset>
  `;
}

function rangeGroup(name, label, minValues, maxValues, activeMin, activeMax, minSuffix, maxSuffix) {
  return `
    <fieldset class="filter-group">
      <legend>${escapeHtml(label)}</legend>
      <div class="range-row">
        <select data-range-min="${escapeHtml(name)}">
          <option value="">下限なし</option>
          ${minValues
            .map((value) => `<option value="${value}" ${String(value) === String(activeMin || "") ? "selected" : ""}>${value}${escapeHtml(minSuffix)}</option>`)
            .join("")}
        </select>
        <select data-range-max="${escapeHtml(name)}">
          <option value="">上限なし</option>
          ${maxValues
            .map((value) => `<option value="${value}" ${String(value) === String(activeMax || "") ? "selected" : ""}>${value}${escapeHtml(maxSuffix)}</option>`)
            .join("")}
        </select>
      </div>
    </fieldset>
  `;
}

function collectSearchFilters(container) {
  return {
    house: container?.querySelector("[data-house].is-active")?.dataset.house || "all",
    proportional: container?.querySelector("[data-proportional].is-active")?.dataset.proportional || "all",
    parties: selectedTokenValues(container, "party"),
    districts: selectedTokenValues(container, "district"),
    ageMin: rangeValue(container, "age", "min"),
    ageMax: rangeValue(container, "age", "max"),
    electionMin: rangeValue(container, "election", "min"),
    electionMax: rangeValue(container, "election", "max"),
    questionMin: rangeValue(container, "question", "min"),
    questionMax: rangeValue(container, "question", "max"),
    governmentRole: container?.querySelector("[data-government-role].is-active")?.dataset.governmentRole || "all"
  };
}

function selectedTokenValues(container, suffix) {
  if (!container) return [];
  return [...container.querySelectorAll(`[data-selected-tokens$="-${suffix}"] [data-token-value]`)].map((token) => token.dataset.tokenValue);
}

function rangeValue(container, suffix, edge) {
  return container?.querySelector(`[data-range-${edge}$="-${suffix}"]`)?.value || "";
}

function bindSearchFilterChips(selector) {
  const container = document.querySelector(selector);
  if (!container) return;
  container.querySelectorAll("[data-house]").forEach((button) => {
    button.addEventListener("click", () => {
      container.querySelectorAll("[data-house]").forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
    });
  });
  container.querySelectorAll("[data-proportional]").forEach((button) => {
    button.addEventListener("click", () => {
      container.querySelectorAll("[data-proportional]").forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
    });
  });
  container.querySelectorAll("[data-government-role]").forEach((button) => {
    button.addEventListener("click", () => {
      container.querySelectorAll("[data-government-role]").forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
    });
  });
  container.querySelectorAll("[data-add-suggestion]").forEach((button) => {
    button.addEventListener("click", () => addSuggestedToken(container, button.dataset.addSuggestion));
  });
  container.querySelectorAll("[data-suggest-input]").forEach((input) => {
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        addSuggestedToken(container, input.dataset.suggestInput);
      }
    });
  });
  container.querySelectorAll("[data-token-value]").forEach((button) => {
    button.addEventListener("click", () => button.remove());
  });
}

function addSuggestedToken(container, groupName) {
  const input = container.querySelector(`[data-suggest-input="${groupName}"]`);
  const list = container.querySelector(`[data-selected-tokens="${groupName}"]`);
  if (!input || !list) return;
  const typedValue = input.value.trim();
  if (!typedValue) return;
  const optionValues = [...container.querySelectorAll(`datalist[id="${groupName}-options"] option`)].map((option) => option.value);
  const value = optionValues.find((option) => option === typedValue) || optionValues.find((option) => option.includes(typedValue));
  if (!value || [...list.querySelectorAll("[data-token-value]")].some((token) => token.dataset.tokenValue === value)) {
    input.value = "";
    return;
  }
  const button = document.createElement("button");
  button.className = "selected-token";
  button.type = "button";
  button.dataset.tokenValue = value;
  button.setAttribute("aria-label", `${value}を削除`);
  button.innerHTML = `${escapeHtml(value)} <span>×</span>`;
  button.addEventListener("click", () => button.remove());
  list.append(button);
  input.value = "";
}

function segmented(activeHouse) {
  return `
    <div class="segmented-control" aria-label="院を選択">
      <button class="chip ${activeHouse === "all" ? "is-active" : ""}" data-house="all">すべて</button>
      <button class="chip ${activeHouse === "shugiin" ? "is-active" : ""}" data-house="shugiin">衆議院</button>
      <button class="chip ${activeHouse === "sangiin" ? "is-active" : ""}" data-house="sangiin">参議院</button>
    </div>
  `;
}

function proportionalSegmented(activeValue) {
  return `
    <div class="segmented-control" aria-label="比例かどうかを選択">
      <button class="chip ${activeValue === "all" ? "is-active" : ""}" data-proportional="all" type="button">すべて</button>
      <button class="chip ${activeValue === "proportional" ? "is-active" : ""}" data-proportional="proportional" type="button">比例</button>
      <button class="chip ${activeValue === "non_proportional" ? "is-active" : ""}" data-proportional="non_proportional" type="button">比例以外</button>
    </div>
  `;
}

function governmentRoleSegmented(activeValue) {
  return `
    <div class="segmented-control" aria-label="政府役職経験の有無を選択">
      <button class="chip ${activeValue === "all" ? "is-active" : ""}" data-government-role="all" type="button">すべて</button>
      <button class="chip ${activeValue === "has" ? "is-active" : ""}" data-government-role="has" type="button">あり</button>
      <button class="chip ${activeValue === "none" ? "is-active" : ""}" data-government-role="none" type="button">なし</button>
      <button class="chip ${activeValue === "prime_minister" ? "is-active" : ""}" data-government-role="prime_minister" type="button">総理大臣</button>
      <button class="chip ${activeValue === "minister" ? "is-active" : ""}" data-government-role="minister" type="button">大臣</button>
      <button class="chip ${activeValue === "senior_vice_minister" ? "is-active" : ""}" data-government-role="senior_vice_minister" type="button">副大臣</button>
      <button class="chip ${activeValue === "parliamentary_vice_minister" ? "is-active" : ""}" data-government-role="parliamentary_vice_minister" type="button">政務官</button>
    </div>
  `;
}

function gauge({ title, totalSeats, rulingSeats, segments }) {
  const majority = Math.floor(totalSeats / 2) + 1;
  const twoThirds = Math.ceil((totalSeats * 2) / 3);
  const oppositionSeats = segments.filter((segment) => segment.alignment === "opposition").reduce((sum, segment) => sum + segment.seats, 0);
  const otherSeats = segments.filter((segment) => segment.alignment === "other").reduce((sum, segment) => sum + segment.seats, 0);
  const reached = rulingSeats >= majority;
  const reachedTwoThirds = rulingSeats >= twoThirds;
  const twoThirdsLine = title === "衆議院" ? thresholdLine(2 / 3, "supermajority-line", "3分の2ライン") : "";
  let cursor = 180;
  const paths = segments
    .map((segment) => {
      const start = cursor;
      const end = cursor + (segment.seats / totalSeats) * 180;
      cursor = end;
      return `<path d="${arcPath(130, 122, 92, start, end)}" stroke="${segment.color}" class="gauge-segment"><title>${escapeHtml(segment.label)}: ${segment.seats}議席</title></path>`;
    })
    .join("");
  return `
    <section class="hud-panel gauge-panel">
      <div class="gauge-heading">
        <h2>${title} 勢力図（2026年5月時点）</h2>
        <div class="status-chip-group">
          <span class="status-chip ${reached ? "success" : "warning"}">過半数到達: ${reached ? "はい" : "いいえ"}</span>
          ${title === "衆議院" ? `<span class="status-chip ${reachedTwoThirds ? "success" : "warning"}">3分の2到達: ${reachedTwoThirds ? "はい" : "いいえ"}</span>` : ""}
        </div>
      </div>
      <svg class="semicircle-gauge" viewBox="0 0 260 150" role="img" aria-label="${title}の勢力図">
        <path d="${arcPath(130, 122, 92, 180, 360)}" class="gauge-track"></path>
        ${paths}
        <line x1="130" y1="18" x2="130" y2="116" class="majority-line"></line>
        <text x="130" y="14" text-anchor="middle" class="gauge-label">過半数ライン</text>
        ${twoThirdsLine}
      </svg>
      <div class="gauge-summary">
        <strong>与党 ${rulingSeats}議席 / 野党 ${oppositionSeats}議席${otherSeats ? ` / その他 ${otherSeats}議席` : ""}</strong>
      </div>
      <div class="seat-legend">
        ${segments
          .map((segment) => `<span><i style="background:${segment.color}"></i>${escapeHtml(shortPartyName(segment.label))} ${segment.seats}</span>`)
          .join("")}
      </div>
    </section>
  `;
}

function thresholdLine(ratio, className, label) {
  const angle = 180 + 180 * ratio;
  const inner = polar(130, 122, 66, angle);
  const outer = polar(130, 122, 106, angle);
  const text = polar(130, 122, 112, angle);
  return `
    <line x1="${inner.x}" y1="${inner.y}" x2="${outer.x}" y2="${outer.y}" class="${className}"></line>
    <text x="${text.x}" y="${text.y}" text-anchor="start" class="gauge-label supermajority-label">${escapeHtml(label)}</text>
  `;
}

function buildGaugeData(title, members, parties) {
  const partyMap = new Map(parties.map((party) => [party.name, party]));
  const counts = new Map();
  for (const member of members) {
    const name = member.party_name || "その他";
    counts.set(name, (counts.get(name) || 0) + 1);
  }
  const segments = [...counts.entries()]
    .map(([label, seats]) => {
      const party = partyMap.get(label);
      return {
        label,
        seats,
        alignment: party?.alignment || (label === "無所属" ? "other" : "opposition"),
        alignmentRank: party?.alignment_rank ?? 999,
        memberCount: party?.alignment_rank_member_count ?? seats
      };
    })
    .sort((a, b) => {
      const groupOrder = { ruling: 0, opposition: 1, other: 2 };
      const groupDiff = groupOrder[a.alignment] - groupOrder[b.alignment];
      if (groupDiff) return groupDiff;
      const rankDiff = a.alignmentRank - b.alignmentRank;
      if (rankDiff) return rankDiff;
      return b.seats - a.seats || a.label.localeCompare(b.label, "ja");
    })
    .map((segment, index) => ({
      ...segment,
      color: segment.alignment === "other" ? "#65708A" : gaugeColors[index % gaugeColors.length]
    }));
  return {
    title,
    totalSeats: members.length,
    rulingSeats: segments.filter((segment) => segment.alignment === "ruling").reduce((sum, segment) => sum + segment.seats, 0),
    segments
  };
}

function rosterTable(items) {
  return `
    <div class="roster-table" role="table" aria-label="議員一覧">
      <div class="table-row table-head" role="row"><span>氏名</span><span>院</span><span>政党・会派</span><span>選挙区</span><span></span></div>
      ${items
        .map(
          (item) => `
        <div class="table-row" role="row">
          <span class="name-cell">${escapeHtml(item.name_kanji)}</span>
          <span>${houseLabel(item.house)}</span>
          <span>${escapeHtml(item.party_short || item.party_name || "未設定")}</span>
          <span>${escapeHtml(item.district_name || "未設定")}</span>
          <button class="text-button" data-open="${item.id}">詳細</button>
        </div>
      `
        )
        .join("")}
    </div>
  `;
}

function rosterCard(item) {
  return `
    <article class="roster-card">
      <div>
        <h3>${escapeHtml(item.name_kanji)}</h3>
        <p>${metaLine(item)}</p>
      </div>
      <button class="text-button" data-open="${item.id}">詳細</button>
    </article>
  `;
}

function featuredFreshmenCards(items) {
  if (!items.length) {
    return `<div class="empty-state">当選1回目の議員データを準備中です。</div>`;
  }
  return items
    .map(
      (item) => `
      <article class="freshman-card">
        <h3>${escapeHtml(item.name_kanji)}</h3>
        <p class="kana">${escapeHtml(item.name_kana || "")}</p>
        <p>${metaLine(item)}</p>
        <span class="freshman-reason">${escapeHtml(formatElectionCount(item))}</span>
        <button class="text-button" data-open="${item.id}">詳細</button>
      </article>
    `
    )
    .join("");
}

function randomFirstTermLegislators(items, count) {
  const candidates = items.filter((item) => Number(item.election_count) === 1);
  return shuffleItems(candidates).slice(0, count);
}

function shuffleItems(items) {
  const shuffled = [...items];
  const cryptoValues = new Uint32Array(shuffled.length);
  if (window.crypto?.getRandomValues) {
    window.crypto.getRandomValues(cryptoValues);
  }
  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const randomValue = cryptoValues[index] || Math.floor(Math.random() * 4294967296);
    const swapIndex = randomValue % (index + 1);
    [shuffled[index], shuffled[swapIndex]] = [shuffled[swapIndex], shuffled[index]];
  }
  return shuffled;
}

function bindOpenDetails() {
  document.querySelectorAll("[data-open]").forEach((button) => {
    button.addEventListener("click", () => navigate({ view: "detail", id: button.dataset.open }));
  });
}

function bindContactForm() {
  const form = document.querySelector(".contact-form");
  if (!form) return;
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const note = form.querySelector(".form-note");
    const formData = new FormData(form);
    const payload = {
      name: String(formData.get("name") || "").trim(),
      organization: String(formData.get("organization") || "").trim() || null,
      type: String(formData.get("type") || ""),
      detail: String(formData.get("detail") || "").trim()
    };
    const subject = `ウシガーへの問い合わせ: ${contactTypeLabel(payload.type)}`;
    const body = [
      "ウシガー運営宛",
      "",
      "以下の内容で問い合わせます。",
      "",
      `お名前: ${payload.name}`,
      `ご所属: ${payload.organization || "未入力"}`,
      `お問い合わせの種類: ${contactTypeLabel(payload.type)}`,
      "",
      "お問い合わせの詳細:",
      payload.detail
    ].join("\n");
    window.location.href = `mailto:contact@ushigaa.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    note.textContent = "メール作成画面を開きました。メールアプリ上で内容をご確認のうえ送信してください。";
  });
}

function contactTypeLabel(value) {
  return {
    "wrong-info": "誤った情報のご指摘",
    improvement: "改善のご要望",
    other: "その他、運営へのお問い合わせ"
  }[value] || "未選択";
}

function bindTopIntro() {
  const aboutLink = document.querySelector("#top-about-link");
  if (!aboutLink) return;
  aboutLink.addEventListener("click", () => navigate({ view: "about" }));
}

function contentPanel(title, lines, options = {}) {
  return `
    <section class="hud-panel content-panel">
      <h2>${escapeHtml(title)}</h2>
      <ul>
        ${lines.map((line) => `<li>${options.allowHtml ? line : escapeHtml(line)}</li>`).join("")}
      </ul>
    </section>
  `;
}

function storySection(title, lines, options = {}) {
  return `
    <section class="story-section">
      <h2>${escapeHtml(title)}</h2>
      <div class="story-lines">
        ${lines.map((line) => `<p>${options.allowHtml ? line : escapeHtml(line)}</p>`).join("")}
      </div>
    </section>
  `;
}

function navInlineLink(label, view) {
  const params = new URLSearchParams({ view });
  return `<a class="inline-link" href="?${params}">${escapeHtml(label)}</a>`;
}

function dataRow(label, value) {
  return `<div><dt>${label}</dt><dd>${escapeHtml(String(value))}</dd></div>`;
}

function formatJapaneseDate(value) {
  const parsed = new Date(`${value}T00:00:00+09:00`);
  if (Number.isNaN(parsed.getTime())) return value || "";
  return `${parsed.getFullYear()}年${parsed.getMonth() + 1}月${parsed.getDate()}日`;
}

function speechPreview(value, length = 180) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (text.length <= length) return text;
  return `${text.slice(0, length)}...`;
}

function speechToHtml(value) {
  return String(value || "")
    .split(/\n{2,}/)
    .map((paragraph) => `<p>${escapeHtml(paragraph)}</p>`)
    .join("");
}

function formatElectionCount(item) {
  if (item.election_count == null) return "未取得";
  return item.election_count_note || `${item.election_count}回`;
}

function formatBirthDate(item) {
  if (!item.birth_date) return "未取得";
  const date = new Date(`${item.birth_date}T00:00:00+09:00`);
  if (Number.isNaN(date.getTime())) return item.birth_date;
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();
  if (item.birth_date_precision === "year") return `${year}年`;
  if (item.birth_date_precision === "month") return `${year}年${month}月`;
  return `${year}年${month}月${day}日`;
}

function calculateAge(item) {
  if (!item?.birth_date) return "未取得";
  const birth = new Date(`${item.birth_date}T00:00:00+09:00`);
  if (Number.isNaN(birth.getTime())) return "未取得";
  const today = new Date();
  if (item.birth_date_precision === "year") {
    const maxAge = today.getFullYear() - birth.getFullYear();
    const minAge = maxAge - 1;
    return `${minAge}〜${maxAge}歳`;
  }
  if (item.birth_date_precision === "month") {
    const firstDayAge = ageOnDate(birth, today);
    const lastDay = new Date(birth.getFullYear(), birth.getMonth() + 1, 0);
    const lastDayAge = ageOnDate(lastDay, today);
    return firstDayAge === lastDayAge ? `${firstDayAge}歳` : `${lastDayAge}〜${firstDayAge}歳`;
  }
  const age = ageOnDate(birth, today);
  return `${age}歳`;
}

function ageOnDate(birth, today) {
  let age = today.getFullYear() - birth.getFullYear();
  const monthDelta = today.getMonth() - birth.getMonth();
  if (monthDelta < 0 || (monthDelta === 0 && today.getDate() < birth.getDate())) age -= 1;
  return age;
}

function matchesAdvancedFilters(item, filters) {
  if (filters.parties?.length && !filters.parties.includes(item.party_name)) return false;
  if (filters.districts?.length && !filters.districts.includes(item.district_name)) return false;
  if (!matchesElectionRange(item, filters.electionMin, filters.electionMax)) return false;
  if (!matchesAgeRange(item, filters.ageMin, filters.ageMax)) return false;
  if (filters.proportional && filters.proportional !== "all" && !matchesProportionalFilter(item, filters.proportional)) return false;
  return true;
}

function matchesGovernmentRoleFilter(item, governmentRole) {
  const hasGovernmentRole = Boolean(item.has_executive_government_experience);
  if (!governmentRole || governmentRole === "all") return true;
  if (governmentRole === "has") return hasGovernmentRole;
  if (governmentRole === "none") return !hasGovernmentRole;
  return Boolean(item[`has_${governmentRole}_experience`]);
}

function matchesProportionalFilter(item, proportional) {
  const isProportional = [item.district_type, item.election_type, item.district_name, item.block_name]
    .filter(Boolean)
    .some((value) => String(value).includes("比例"));
  return proportional === "proportional" ? isProportional : !isProportional;
}

function matchesAgeRange(item, minValue, maxValue) {
  if (!minValue && !maxValue) return true;
  const ageRange = getAgeRange(item);
  if (!ageRange) return false;
  const min = minValue ? Number(minValue) : 0;
  const max = maxValue ? Number(maxValue) : 200;
  return ageRange.min <= max && ageRange.max >= min;
}

function matchesElectionRange(item, minValue, maxValue) {
  if (!minValue && !maxValue) return true;
  const count = Number(item.election_count);
  if (!Number.isFinite(count)) return false;
  const min = minValue ? Number(minValue) : 0;
  const max = maxValue ? Number(maxValue) : 999;
  return count >= min && count <= max;
}

function getAgeRange(item) {
  if (!item?.birth_date) return null;
  const birth = new Date(`${item.birth_date}T00:00:00+09:00`);
  if (Number.isNaN(birth.getTime())) return null;
  const today = new Date();
  if (item.birth_date_precision === "year") {
    const max = today.getFullYear() - birth.getFullYear();
    return { min: max - 1, max };
  }
  if (item.birth_date_precision === "month") {
    const firstDayAge = ageOnDate(birth, today);
    const lastDay = new Date(birth.getFullYear(), birth.getMonth() + 1, 0);
    const lastDayAge = ageOnDate(lastDay, today);
    return { min: Math.min(firstDayAge, lastDayAge), max: Math.max(firstDayAge, lastDayAge) };
  }
  const age = ageOnDate(birth, today);
  return { min: age, max: age };
}

function sourceLabel(sourceType, house) {
  if (sourceType === "diet_official") return `${houseLabel(house)}公式サイト`;
  if (sourceType === "party_official") return "政党公式サイト";
  if (sourceType === "personal_official") return "本人公式サイト";
  return "出典未取得";
}

function options(values, activeValue) {
  const uniqueValues = [...new Set(values.filter(Boolean))].sort((a, b) => a.localeCompare(b, "ja"));
  return [
    `<option value="">すべて</option>`,
    ...uniqueValues.map((value) => `<option value="${escapeHtml(value)}" ${value === activeValue ? "selected" : ""}>${escapeHtml(value)}</option>`)
  ].join("");
}

function houseLabel(house) {
  return house === "shugiin" ? "衆議院" : "参議院";
}

function districtTypeLabel(type) {
  if (type === "proportional" || type === "比例代表") return "比例選出";
  if (type === "single" || type === "小選挙区" || type === "選挙区") return "選挙区選出";
  return type || "未設定";
}

function shortPartyName(name) {
  return String(name)
    .replace("自由民主党", "自民")
    .replace("日本維新の会", "維新")
    .replace("立憲民主党", "立憲")
    .replace("国民民主党・無所属クラブ", "国民")
    .replace("国民民主党・新緑風会", "国民")
    .replace("国民民主党", "国民")
    .replace("日本共産党", "共産");
}

function metaLine(item) {
  const questionCount = Number.isInteger(item.kokkai_question_count) ? `2023年以降の国会質疑 ${item.kokkai_question_count}件` : "";
  const governmentRole = governmentRoleLabel(item);
  return [houseLabel(item.house), item.party_name, item.district_name, questionCount, governmentRole].filter(Boolean).map(escapeHtml).join(" / ");
}

function governmentRoleLabel(item) {
  if (item.has_prime_minister_experience) return "2023年以降の総理大臣経験あり";
  if (item.has_minister_experience) return "2023年以降の大臣経験あり";
  if (item.has_senior_vice_minister_experience) return "2023年以降の副大臣経験あり";
  if (item.has_parliamentary_vice_minister_experience) return "2023年以降の政務官経験あり";
  return "";
}

function arcPath(cx, cy, r, startAngle, endAngle) {
  const start = polar(cx, cy, r, startAngle);
  const end = polar(cx, cy, r, endAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArcFlag} 1 ${end.x} ${end.y}`;
}

function polar(cx, cy, r, angle) {
  const radians = (angle * Math.PI) / 180;
  return {
    x: cx + r * Math.cos(radians),
    y: cy + r * Math.sin(radians)
  };
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function fallbackBanner() {
  if (!apiOffline) return "";
  return `<div class="fallback-banner">オフラインデータ表示中</div>`;
}
