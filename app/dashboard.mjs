import { parseDashboardCsv } from "./data.mjs";

const byId = (id) => document.getElementById(id);
const pages = ["intro", "method", "results", "screen"];
const dataset = new URL("../outputs/final_dataset.csv", import.meta.url);
const pct = new Intl.NumberFormat("en-US", { style: "percent", maximumFractionDigits: 2 });
const number = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 });

let entities = [];
let plotted = [];
let byRssd = new Map();
let selectedId;
let sortKey = "uninsured_dep_share";
let sortOrder = -1;

const percent = (value) => value == null ? "—" : pct.format(value);
const assets = (value) => value == null ? "—" : number.format(value);
const bankLabel = (row) => row.ticker || row.name;

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text != null) node.textContent = text;
  if (className) node.className = className;
  return node;
}

function sampleStatus(row) {
  if (row.in_sample) return "In sample";
  const reasons = [];
  if (!row.has_fdic) reasons.push("No FDIC match");
  if (!row.has_returns) reasons.push("No event returns");
  if (row.has_fdic && !row.positive_equity) reasons.push("Equity not positive");
  return reasons.join(" · ") || "Outside sample";
}

function showPage(moveFocus = false) {
  const requested = location.hash.slice(1);
  const page = pages.includes(requested) ? requested : "intro";
  for (const id of pages) byId(id).hidden = id !== page;
  for (const link of document.querySelectorAll(".navigation a")) {
    if (link.hash === "#" + page) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
  if (moveFocus) {
    const heading = byId(page + "-title");
    heading.setAttribute("tabindex", "-1");
    heading.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  }
  if (page === "results") requestAnimationFrame(drawChart);
}

function updateSelection() {
  for (const point of byId("plot").querySelectorAll("[data-rssd]")) {
    point.setAttribute("aria-pressed", String(point.dataset.rssd === selectedId));
  }
  for (const label of byId("plot").querySelectorAll("[data-label-for]")) {
    label.toggleAttribute("hidden", label.dataset.labelFor !== selectedId && label.dataset.imputed !== "true");
  }
}

function setBank(rssdId) {
  const row = byRssd.get(rssdId);
  if (!row) return;
  selectedId = rssdId;
  byId("bank-select").value = rssdId;
  const list = element("dl", null, "detail-pairs");
  const metrics = [
    ["Uninsured share", percent(row.uninsured_dep_share)],
    ["Securities loss / equity", percent(row.sec_loss_to_equity)],
    ["Assets ($B)", assets(row.total_assets_bn)],
    ["Event BHAR", percent(row.bhar_0_2)],
    ["Buy-and-hold return", percent(row.bhr_0_2)],
  ];
  for (const [label, value] of metrics) {
    const pair = element("div");
    pair.append(element("dt", label), element("dd", value));
    list.append(pair);
  }
  const details = byId("bank-details");
  details.replaceChildren(element("h3", row.name), list, element("p", sampleStatus(row), "muted"));
  if (row.dlret_imputed) {
    details.append(element("p", "Imputed delisting return: the pipeline assumes a total loss at delisting. The BHAR also accounts for the market’s return.", "detail-note"));
  }
  updateSelection();
}

function svgElement(tag, attrs, text) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [name, value] of Object.entries(attrs)) node.setAttribute(name, value);
  if (text != null) node.textContent = text;
  return node;
}

// Round the display bounds out to 5 percentage points; never clip an observation.
function axis(values, tickStep) {
  const paddingStep = 0.05;
  const min = Math.floor(Math.min(0, ...values) / paddingStep) * paddingStep;
  const max = Math.max(min + paddingStep, Math.ceil(Math.max(0, ...values) / paddingStep) * paddingStep);
  const ticks = [];
  for (let i = Math.ceil(min / tickStep); i <= Math.floor(max / tickStep); i++) ticks.push(i * tickStep);
  return { min, max, ticks };
}

function drawChart() {
  const plot = byId("plot");
  const width = plot.clientWidth;
  if (!entities.length || !width) return;
  if (!plotted.length) {
    plot.replaceChildren(element("p", "No in-sample banks have both an event BHAR and an uninsured deposit share.", "muted plot-empty"));
    return;
  }
  const height = width < 440 ? 350 : 430;
  const left = width < 440 ? 54 : 68;
  const right = width - 16;
  const top = 20;
  const bottom = height - 51;
  const xAxis = axis(plotted.map((row) => row.uninsured_dep_share), 0.2);
  const yAxis = axis(plotted.map((row) => row.bhar_0_2), 0.2);
  const x = (value) => left + 9 + (value - xAxis.min) / (xAxis.max - xAxis.min) * (right - left - 18);
  const y = (value) => top + 8 + (yAxis.max - value) / (yAxis.max - yAxis.min) * (bottom - top - 16);
  const svg = svgElement("svg", {
    viewBox: "0 0 " + width + " " + height,
    role: "group",
    "aria-label": "Scatterplot of March 2023 buy-and-hold abnormal return versus uninsured domestic deposit share",
  });
  for (const value of yAxis.ticks) {
    const zero = value === 0;
    svg.append(
      svgElement("line", { x1: left, y1: y(value), x2: right, y2: y(value), stroke: zero ? "#7c9588" : "#e0e9e0", "stroke-dasharray": zero ? "4 3" : "none" }),
      svgElement("text", { x: left - 6, y: y(value) + 4, "text-anchor": "end" }, percent(value)),
    );
  }
  for (const value of xAxis.ticks) {
    svg.append(
      svgElement("line", { x1: x(value), y1: top, x2: x(value), y2: bottom, stroke: "#e0e9e0" }),
      svgElement("text", { x: x(value), y: bottom + 17, "text-anchor": "middle" }, percent(value)),
    );
  }
  svg.append(
    svgElement("line", { x1: left, y1: bottom, x2: right, y2: bottom, stroke: "#7c9588" }),
    svgElement("text", { x: (left + right) / 2, y: height - 11, "text-anchor": "middle", class: "axis-title" }, "Uninsured domestic deposit share"),
    svgElement("text", { x: 10, y: (top + bottom) / 2, transform: "rotate(-90 10 " + (top + bottom) / 2 + ")", "text-anchor": "middle", class: "axis-title" }, "March 2023 BHAR"),
  );

  const maxAssets = Math.max(1, ...plotted.map((row) => row.total_assets_bn ?? 0));
  const losses = plotted.map((row) => row.sec_loss_to_equity).filter((value) => value != null).sort((a, b) => a - b);
  const low = losses[0] ?? 0;
  const high = losses[Math.ceil(0.95 * losses.length) - 1] ?? low;
  byId("loss-legend").textContent = losses.length
    ? "Darker = higher securities loss / equity; darkest at " + percent(high) + " and above"
    : "Securities loss / equity unavailable";
  const light = [143, 185, 154], dark = [23, 84, 64];
  const imputed = plotted.filter((row) => row.dlret_imputed).sort((a, b) => a.uninsured_dep_share - b.uninsured_dep_share);
  const labels = svgElement("g", { "aria-hidden": "true", "pointer-events": "none" });
  // Draw the largest dots first so nearby small banks remain visible.
  for (const row of [...plotted].sort((a, b) => (b.total_assets_bn ?? 0) - (a.total_assets_bn ?? 0))) {
    const px = x(row.uninsured_dep_share);
    const py = y(row.bhar_0_2);
    const radius = Math.sqrt(9 + 135 * Math.max(0, row.total_assets_bn ?? 0) / maxAssets);
    const shade = high === low ? 0.5 : Math.max(0, Math.min(1, (row.sec_loss_to_equity - low) / (high - low)));
    const fill = row.sec_loss_to_equity == null ? "#c4c9c6" : "rgb(" + light.map((v, i) => Math.round(v + (dark[i] - v) * shade)).join(",") + ")";
    const description = bankLabel(row) + ": BHAR " + percent(row.bhar_0_2)
      + ", uninsured share " + percent(row.uninsured_dep_share)
      + ", securities loss / equity " + percent(row.sec_loss_to_equity)
      + ", assets ($B) " + assets(row.total_assets_bn)
      + (row.dlret_imputed ? " · imputed delisting return" : "");
    const point = svgElement("g", {
      role: "button", tabindex: -1, "aria-label": description, "data-rssd": row.rssd_id,
      "data-bank": bankLabel(row), "data-imputed": String(row.dlret_imputed === true),
    });
    point.append(svgElement("title", {}, description), svgElement("circle", { cx: px, cy: py, r: radius, fill }));
    point.addEventListener("click", () => setBank(row.rssd_id));
    point.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        setBank(row.rssd_id);
      }
    });
    svg.append(point);

    const labelOnLeft = row.dlret_imputed ? row === imputed[0] : px > width * 0.74;
    labels.append(svgElement("text", {
      x: px + (labelOnLeft ? -radius - 4 : radius + 4),
      y: py - radius - 4,
      "text-anchor": labelOnLeft ? "end" : "start",
      class: "ticker-label",
      "data-label-for": row.rssd_id,
      "data-imputed": String(row.dlret_imputed === true),
    }, bankLabel(row)));
  }
  svg.append(labels);
  plot.replaceChildren(svg);
  updateSelection();
}

function renderTable() {
  const query = byId("bank-filter").value.trim().toLowerCase();
  const scope = byId("sample-filter").value;
  const rows = entities.filter((row) => {
    if (scope === "included" && !row.in_sample) return false;
    if (scope === "excluded" && row.in_sample) return false;
    return (row.ticker + " " + row.name).toLowerCase().includes(query);
  });
  rows.sort((a, b) => {
    const tie = () => bankLabel(a).localeCompare(bankLabel(b)) || a.rssd_id.localeCompare(b.rssd_id);
    if (sortKey === "bank") return sortOrder * tie();
    const left = a[sortKey], right = b[sortKey];
    if (left == null || right == null) return (left == null) - (right == null) || tie();
    return sortOrder * (left - right) || tie();
  });
  byId("table-count").textContent = rows.length + " of " + entities.length + " entities · December 2022 Call Reports";
  const tableRows = rows.map((row) => {
    const bankCell = element("td");
    bankCell.append(element("span", bankLabel(row), "bank-ticker"));
    if (row.ticker) bankCell.append(element("span", row.name, "bank-name"));
    const tr = element("tr");
    tr.append(bankCell, ...[
      percent(row.uninsured_dep_share), percent(row.sec_loss_to_equity),
      percent(row.htm_loss_to_equity), assets(row.total_assets_bn), sampleStatus(row),
    ].map((value) => element("td", value)));
    return tr;
  });
  if (!tableRows.length) {
    const td = element("td", "No matching entities.", "empty-cell");
    td.colSpan = 6;
    const tr = element("tr");
    tr.append(td);
    tableRows.push(tr);
  }
  byId("bank-rows").replaceChildren(...tableRows);
  for (const button of document.querySelectorAll("[data-sort]")) {
    const active = button.dataset.sort === sortKey;
    if (active) button.parentElement.setAttribute("aria-sort", sortOrder === 1 ? "ascending" : "descending");
    else button.parentElement.removeAttribute("aria-sort");
    button.lastElementChild.textContent = active ? (sortOrder === 1 ? "↑" : "↓") : "↕";
  }
}

function populateDashboard() {
  byRssd = new Map(entities.map((row) => [row.rssd_id, row]));
  const included = entities.filter((row) => row.in_sample);
  plotted = included.filter((row) => row.bhar_0_2 != null && row.uninsured_dep_share != null);
  const omitted = included.length - plotted.length;
  const imputed = plotted.filter((row) => row.dlret_imputed);
  byId("intro-count").textContent = entities.length;
  byId("intro-coverage").textContent = included.length;
  byId("intro-source").textContent = "CRSP event study · December 2022 Call Reports";
  byId("results-status").textContent = plotted.length + " of " + entities.length + " entities plotted. "
    + (entities.length - included.length) + " outside the analysis sample."
    + (omitted ? " " + omitted + " in-sample entities lack a chart value." : "");
  if (imputed.length) {
    byId("imputed-note").textContent = imputed.map((row) => bankLabel(row) + " " + percent(row.bhar_0_2)).join(" · ")
      + " — outlined because the pipeline imputes their missing delisting returns.";
    byId("imputed-note").hidden = false;
  }

  byId("bank-select").replaceChildren(...[...entities].sort((a, b) => bankLabel(a).localeCompare(bankLabel(b))).map((row) => {
    const option = element("option", row.ticker ? row.ticker + " · " + row.name : row.name);
    option.value = row.rssd_id;
    return option;
  }));
  byId("results-grid").hidden = false;
  byId("screen-card").hidden = false;
  byId("screen-status").hidden = true;
  setBank((imputed[0] ?? plotted[0] ?? entities[0]).rssd_id);
  renderTable();
  drawChart();
}

async function start() {
  try {
    const response = await fetch(dataset, { cache: "no-store" });
    if (!response.ok) throw new Error("final_dataset.csv returned HTTP " + response.status + ".");
    entities = parseDashboardCsv(await response.text());
    populateDashboard();
  } catch (error) {
    const message = "Could not load the dashboard data. Run python3 app/serve.py and check outputs/final_dataset.csv. " + error.message;
    for (const id of ["intro-source", "results-status", "screen-status"]) byId(id).textContent = message;
  }
}

window.addEventListener("hashchange", () => showPage(true));
document.querySelector(".skip-link").addEventListener("click", (event) => {
  event.preventDefault();
  byId("content").focus();
});
byId("bank-filter").addEventListener("input", renderTable);
byId("sample-filter").addEventListener("change", renderTable);
byId("bank-select").addEventListener("change", (event) => setBank(event.target.value));
for (const button of document.querySelectorAll("[data-sort]")) {
  button.addEventListener("click", () => {
    sortOrder = sortKey === button.dataset.sort ? -sortOrder : button.dataset.sort === "bank" ? 1 : -1;
    sortKey = button.dataset.sort;
    renderTable();
  });
}
new ResizeObserver(() => requestAnimationFrame(drawChart)).observe(byId("plot"));
showPage();
start();
