import { parseDashboardCsv } from "./data.mjs";

const byId = (id) => document.getElementById(id);
const pages = ["intro", "method", "results", "screen"];
const specs = {
  crsp: {
    file: "poc_crsp_rows.csv",
    label: "CRSP preview",
    benchmark: "CRSP value-weighted market model",
  },
  original: {
    file: "poc_final_rows.csv",
    label: "Original yfinance sample",
    benchmark: "SPY market model (yfinance)",
  },
};
const datasets = new Map();
let activeSource;
let balanceSheets = [];
let selectedTicker;
let sortKey = "uninsured_dep_share";
let sortOrder = -1;

const pct = new Intl.NumberFormat("en-US", { style: "percent", maximumFractionDigits: 2 });
const number = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });
const reportMonth = new Intl.DateTimeFormat("en-US", { month: "long", year: "numeric", timeZone: "UTC" });
const percent = (value) => value == null ? "—" : pct.format(value);
const assets = (value) => value == null ? "—" : number.format(value);
const missingText = (row) => row.car_note || "Incomplete event returns";

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text != null) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function showPage(moveFocus = false) {
  const requested = location.hash.slice(1);
  const page = pages.includes(requested) ? requested : "intro";
  for (const id of pages) byId(id).hidden = id !== page;
  for (const link of document.querySelectorAll(".navigation a")) {
    if (link.hash === `#${page}`) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
  if (moveFocus) {
    const heading = byId(`${page}-title`);
    heading.setAttribute("tabindex", "-1");
    heading.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  }
  if (page === "results") requestAnimationFrame(drawChart);
}

window.addEventListener("hashchange", () => showPage(true));
document.querySelector(".skip-link").addEventListener("click", (event) => {
  event.preventDefault();
  byId("content").focus();
});
showPage();

async function readDataset(key, spec) {
  const response = await fetch(new URL(`../outputs/${spec.file}`, import.meta.url), { cache: "no-cache" });
  if (key === "crsp" && response.status === 404) return;
  if (!response.ok) throw new Error(`${spec.file} could not be loaded (HTTP ${response.status}).`);
  const rows = parseDashboardCsv(await response.text());
  if (rows.some((row) => row.call_report_date !== "2022-12-31")) {
    throw new Error(`${spec.file} must contain December 2022 call reports for this event study.`);
  }
  datasets.set(key, rows);
}

function updateResults() {
  const rows = datasets.get(activeSource);
  const spec = specs[activeSource];
  const complete = rows.filter((row) => row.car_0_2 != null);
  const missing = rows.filter((row) => row.car_0_2 == null);
  const plottable = complete.filter((row) => row.uninsured_dep_share != null);
  const incomplete = missing.length ? ` Missing return: ${missing.map((row) => row.ticker).join(", ")}.` : "";
  const noDeposits = complete.length - plottable.length;
  byId("intro-quarter").textContent = reportMonth.format(new Date(balanceSheets[0].call_report_date));
  byId("intro-count").textContent = rows.length;
  byId("intro-coverage").textContent = `${complete.length}/${rows.length}`;
  byId("intro-source").textContent = `${spec.label} · March 2023 event window`;
  byId("results-status").textContent = `Prototype · ${plottable.length} of ${rows.length} banks plotted.${incomplete}${noDeposits ? ` ${noDeposits} with returns lack a deposit measure.` : ""} This small sample is descriptive.`;
  byId("chart-method").textContent = `Summed cumulative abnormal return · ${spec.benchmark}`;
  byId("results-grid").hidden = false;
  if (!rows.some((row) => row.ticker === selectedTicker)) {
    selectedTicker = plottable[0]?.ticker ?? rows[0].ticker;
  }
  const bankSelect = byId("bank-select");
  bankSelect.replaceChildren(...rows.map((row) => {
    const option = element("option", `${row.ticker} · ${row.entity_name}`);
    option.value = row.ticker;
    return option;
  }));
  setBank(selectedTicker);
}

function setBank(ticker) {
  selectedTicker = ticker;
  const row = datasets.get(activeSource).find((entry) => entry.ticker === ticker);
  byId("bank-select").value = ticker;
  const list = element("dl", null, "detail-pairs");
  const metrics = [
    ["Uninsured share", percent(row.uninsured_dep_share)],
    ["Securities loss / equity", percent(row.sec_loss_to_equity)],
    ["Assets ($B)", assets(row.total_assets_bn)],
    ["Event CAR", percent(row.car_0_2)],
  ];
  for (const [label, value] of metrics) {
    const pair = element("div");
    pair.append(element("dt", label), element("dd", value));
    list.append(pair);
  }
  const details = byId("bank-details");
  details.replaceChildren(element("h3", row.entity_name), list);
  if (row.car_0_2 == null) details.append(element("p", missingText(row), "muted"));
  for (const point of byId("plot").querySelectorAll("[data-bank]")) {
    const active = point.dataset.bank === ticker;
    point.setAttribute("aria-pressed", String(active));
    point.querySelector("circle").setAttribute("stroke-width", active ? 3 : 1.2);
  }
}

function svgElement(tag, attrs, text) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, value);
  if (text != null) node.textContent = text;
  return node;
}

function axis(values, step, includeZero = false) {
  const min = Math.min(...values, ...(includeZero ? [0] : []));
  const max = Math.max(...values, ...(includeZero ? [0] : []));
  const tickStep = Math.max(step, Math.ceil((max - min) / (5 * step)) * step);
  const start = Math.floor((min + 1e-9) / tickStep);
  const end = Math.max(start + 1, Math.ceil((max - 1e-9) / tickStep));
  return {
    min: start * tickStep,
    max: end * tickStep,
    ticks: Array.from({ length: end - start + 1 }, (_, i) => (start + i) * tickStep),
  };
}

function drawChart() {
  const plot = byId("plot");
  if (!activeSource || !plot.clientWidth) return;
  const rows = datasets.get(activeSource).filter((row) => row.car_0_2 != null && row.uninsured_dep_share != null);
  if (!rows.length) {
    plot.replaceChildren(element("p", "No banks have both a usable event return and an uninsured deposit share.", "muted plot-empty"));
    return;
  }
  const width = plot.clientWidth;
  const height = width < 440 ? 275 : 337;
  const left = width < 440 ? 56 : 70;
  const right = width - 27;
  const top = 32;
  const bottom = height - 53;
  const xAxis = axis(rows.map((row) => row.uninsured_dep_share), 0.05);
  const yAxis = axis(rows.map((row) => row.car_0_2), 0.2, true);
  // Leave room for bubble radii and labels at the edges of the chart.
  const x = (value) => left + 13 + (value - xAxis.min) / (xAxis.max - xAxis.min) * (right - left - 26);
  const y = (value) => top + 8 + (yAxis.max - value) / (yAxis.max - yAxis.min) * (bottom - top - 16);
  const svg = svgElement("svg", {
    viewBox: `0 0 ${width} ${height}`, role: "group",
    "aria-label": "Scatterplot of March 2023 CAR versus uninsured domestic deposit share",
  });
  for (const value of yAxis.ticks) {
    const zero = Math.abs(value) < 1e-8;
    svg.append(
      svgElement("line", { x1: left, y1: y(value), x2: right, y2: y(value), stroke: zero ? "#7c9588" : "#e0e9e0", "stroke-dasharray": zero ? "4 3" : "none" }),
      svgElement("text", { x: left - 8, y: y(value) + 4, "text-anchor": "end" }, percent(value)),
    );
  }
  for (const value of xAxis.ticks) {
    svg.append(
      svgElement("line", { x1: x(value), y1: top, x2: x(value), y2: bottom, stroke: "#e0e9e0" }),
      svgElement("text", { x: x(value), y: bottom + 18, "text-anchor": "middle" }, percent(value)),
    );
  }
  svg.append(
    svgElement("line", { x1: left, y1: bottom, x2: right, y2: bottom, stroke: "#7c9588" }),
    svgElement("text", { x: (left + right) / 2, y: height - 11, "text-anchor": "middle", class: "axis-title" }, "Uninsured domestic deposit share"),
    svgElement("text", { x: 12, y: (top + bottom) / 2, transform: `rotate(-90 12 ${(top + bottom) / 2})`, "text-anchor": "middle", class: "axis-title" }, "March 2023 CAR"),
  );

  const maxAssets = Math.max(1, ...rows.map((row) => row.total_assets_bn ?? 0));
  const losses = rows.flatMap((row) => row.sec_loss_to_equity == null ? [] : [row.sec_loss_to_equity]);
  const low = losses.length ? Math.min(...losses) : 0;
  const high = losses.length ? Math.max(...losses) : 0;
  const light = [159, 196, 170], dark = [40, 96, 78];
  for (const row of [...rows].sort((a, b) => (b.total_assets_bn ?? 0) - (a.total_assets_bn ?? 0))) {
    const px = x(row.uninsured_dep_share), py = y(row.car_0_2);
    const radius = Math.sqrt(32 + 265 * Math.max(0, row.total_assets_bn ?? 0) / maxAssets);
    const ratio = high === low ? 0.5 : (row.sec_loss_to_equity - low) / (high - low);
    const color = row.sec_loss_to_equity == null ? "#c4c9c6" : `rgb(${light.map((v, i) => Math.round(v + (dark[i] - v) * ratio)).join(",")})`;
    const description = `${row.ticker}: CAR ${percent(row.car_0_2)}, uninsured share ${percent(row.uninsured_dep_share)}, securities loss / equity ${percent(row.sec_loss_to_equity)}, assets ($B) ${assets(row.total_assets_bn)}`;
    const point = svgElement("g", {
      tabindex: 0, role: "button", "aria-label": description, "data-bank": row.ticker,
      "aria-pressed": String(row.ticker === selectedTicker),
    });
    point.append(
      svgElement("title", {}, description),
      svgElement("circle", { cx: px, cy: py, r: radius, fill: color, stroke: "#142d2b", "stroke-width": row.ticker === selectedTicker ? 3 : 1.2 }),
      svgElement("text", { x: px, y: py - radius - 5, "text-anchor": "middle", class: "ticker-label", "aria-hidden": "true" }, row.ticker),
    );
    point.addEventListener("click", () => setBank(row.ticker));
    point.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        setBank(row.ticker);
      }
    });
    svg.append(point);
  }
  plot.replaceChildren(svg);
}

function renderTable() {
  const query = byId("bank-filter").value.trim().toLowerCase();
  const rows = balanceSheets.filter((row) => `${row.ticker} ${row.entity_name}`.toLowerCase().includes(query));
  rows.sort((a, b) => {
    const left = a[sortKey], right = b[sortKey];
    if (left == null || right == null) return (left == null) - (right == null) || a.ticker.localeCompare(b.ticker);
    const cmp = typeof left === "number" ? left - right : left.localeCompare(right);
    return sortOrder * cmp || a.ticker.localeCompare(b.ticker);
  });
  byId("table-count").textContent = `${rows.length} of ${balanceSheets.length} banks · December 2022 Call Reports`;
  const tableRows = rows.map((row) => {
    const bankCell = element("td");
    bankCell.append(element("span", row.ticker, "bank-ticker"), element("span", row.entity_name, "bank-name"));
    const tr = element("tr");
    tr.append(bankCell, ...[
      percent(row.uninsured_dep_share), percent(row.sec_loss_to_equity),
      percent(row.htm_loss_to_equity), assets(row.total_assets_bn), row.call_report_date,
    ].map((value) => element("td", value)));
    return tr;
  });
  if (!tableRows.length) {
    const td = element("td", "No matching banks.", "empty-cell");
    td.colSpan = 6;
    const tr = element("tr");
    tr.append(td);
    tableRows.push(tr);
  }
  byId("bank-rows").replaceChildren(...tableRows);
  for (const button of document.querySelectorAll("[data-sort]")) {
    const isActive = button.dataset.sort === sortKey;
    if (isActive) button.parentElement.setAttribute("aria-sort", sortOrder === 1 ? "ascending" : "descending");
    else button.parentElement.removeAttribute("aria-sort");
    button.lastElementChild.textContent = isActive ? (sortOrder === 1 ? "↑" : "↓") : "↕";
  }
}

byId("bank-filter").addEventListener("input", renderTable);
for (const button of document.querySelectorAll("[data-sort]")) {
  button.addEventListener("click", () => {
    sortOrder = sortKey === button.dataset.sort ? -sortOrder : button.dataset.sort === "ticker" ? 1 : -1;
    sortKey = button.dataset.sort;
    renderTable();
  });
}
byId("bank-select").addEventListener("change", (event) => setBank(event.target.value));
byId("return-source").addEventListener("change", (event) => {
  activeSource = event.target.value;
  updateResults();
  drawChart();
});
new ResizeObserver(() => requestAnimationFrame(drawChart)).observe(byId("plot"));

function sameBalanceSheets(original, preview) {
  const fields = ["entity_name", "call_report_date", "total_assets_bn", "uninsured_dep_share", "sec_loss_to_equity", "htm_loss_to_equity"];
  const byTicker = new Map(original.map((row) => [row.ticker, row]));
  return original.length === preview.length && preview.every((row) => {
    const base = byTicker.get(row.ticker);
    return base && fields.every((field) => row[field] === base[field]);
  });
}

async function start() {
  const outcomes = await Promise.allSettled(Object.entries(specs).map(([key, spec]) => readDataset(key, spec)));
  const failures = outcomes.filter((outcome) => outcome.status === "rejected").map((outcome) => outcome.reason.message);
  if (!datasets.size) {
    const message = `The dashboard data could not load. Serve the repository root over HTTP and check outputs/poc_final_rows.csv. ${failures.join(" ")}`;
    for (const id of ["intro-source", "results-status", "screen-status"]) byId(id).textContent = message;
    return;
  }
  if (datasets.has("original") && datasets.has("crsp")
      && !sameBalanceSheets(datasets.get("original"), datasets.get("crsp"))) {
    datasets.delete("crsp");
    failures.push("The CRSP preview was generated from a different balance-sheet sample. Rebuild it to compare both return sources.");
  }
  const keys = Object.keys(specs).filter((key) => datasets.has(key));
  activeSource = keys[0];
  balanceSheets = datasets.get("original") ?? datasets.get(activeSource);
  byId("return-source").replaceChildren(...keys.map((key) => {
    const option = element("option", specs[key].label);
    option.value = key;
    return option;
  }));
  byId("source-control").hidden = keys.length < 2;
  byId("screen-status").hidden = true;
  if (failures.length) {
    const warning = element("p", failures.join(" "), "notice method-note");
    byId("results-status").after(warning);
  }
  byId("screen-card").hidden = false;
  updateResults();
  renderTable();
  drawChart();
}

start();
