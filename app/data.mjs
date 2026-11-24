const textColumns = ["rssd_id", "ticker", "name"];
const numericColumns = [
  "total_assets_bn",
  "uninsured_dep_share",
  "sec_loss_to_equity",
  "htm_loss_to_equity",
  "bhar_0_2",
];
const booleanColumns = ["in_sample", "main_sample", "dlret_imputed", "has_fdic", "has_returns", "positive_equity"];
const optionalNumericColumns = ["bhr_0_2", "car_0_2", "n_event_days"];
const optionalBooleanColumns = ["delisted_in_window"];
// The pipeline has no delisting flags for rows without CRSP return observations.
const nullableBooleans = new Set(["dlret_imputed", "delisted_in_window"]);
const decimal = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/;

function csvRecords(text) {
  const records = [];
  let record = [];
  let field = "";
  let state = "start";

  function endField() {
    record.push(field);
    field = "";
    state = "start";
  }

  function endRecord() {
    if (!record.length && state === "start") return; // Skip empty lines.
    endField();
    records.push(record);
    record = [];
  }

  // Only unquoted commas and line breaks end fields and records.
  const source = text.replace(/^\uFEFF/, "");
  for (let i = 0; i < source.length; i++) {
    const char = source[i];
    if (state === "quoted") {
      if (char === '"' && source[i + 1] === '"') {
        field += '"';
        i++;
      } else if (char === '"') {
        state = "closed";
      } else {
        field += char;
      }
    } else if (char === ",") {
      endField();
    } else if (char === "\n" || char === "\r") {
      endRecord();
      if (char === "\r" && source[i + 1] === "\n") i++;
    } else if (char === '"' && state === "start") {
      state = "quoted";
    } else if (char === '"' || state === "closed") {
      throw new Error(`CSV record ${records.length + 1} has invalid quoting.`);
    } else {
      field += char;
      state = "plain";
    }
  }

  if (state === "quoted") throw new Error("The CSV has an unclosed quoted field.");
  endRecord();
  return records;
}

/** Read one dashboard output row per RSSD ID. Keep missing values distinct from zero and false. */
export function parseDashboardCsv(text) {
  const [header = [], ...records] = csvRecords(text);
  const headers = header.map((value) => value.trim());
  const column = new Map(headers.map((name, index) => [name, index]));
  const requiredColumns = [...textColumns, ...numericColumns, ...booleanColumns];
  const missing = requiredColumns.filter((name) => !column.has(name));
  if (missing.length) throw new Error(`Missing CSV columns: ${missing.join(", ")}.`);
  if (column.size !== headers.length) throw new Error("The CSV has duplicate column names.");
  if (!records.length) throw new Error("The CSV has no bank rows.");

  const numbers = [...numericColumns, ...optionalNumericColumns.filter((name) => column.has(name))];
  const booleans = [...booleanColumns, ...optionalBooleanColumns.filter((name) => column.has(name))];
  const rssdIds = new Set();
  return records.map((record, index) => {
    const label = `CSV record ${index + 2}`;
    if (record.length !== headers.length) {
      throw new Error(`${label} has ${record.length} columns; expected ${headers.length}.`);
    }

    const read = (name) => record[column.get(name)];
    const row = { rssd_id: read("rssd_id").trim(), ticker: read("ticker"), name: read("name") };
    if (!row.rssd_id) throw new Error(`${label} is missing an RSSD ID.`);
    if (rssdIds.has(row.rssd_id)) throw new Error(`${label} repeats RSSD ID ${row.rssd_id}.`);
    rssdIds.add(row.rssd_id);

    for (const name of numbers) {
      const value = read(name).trim();
      if (value === "") {
        row[name] = null;
      } else {
        const number = Number(value);
        if (!decimal.test(value) || !Number.isFinite(number)) {
          throw new Error(`${label} has an invalid number in ${name}.`);
        }
        row[name] = number;
      }
    }

    for (const name of booleans) {
      const value = read(name).trim().toLowerCase();
      if (value === "true" || value === "false") {
        row[name] = value === "true";
      } else if (value === "" && nullableBooleans.has(name)) {
        row[name] = null;
      } else {
        throw new Error(`${label} has an invalid boolean in ${name}; expected True or False.`);
      }
    }
    return row;
  });
}

/** Read comparable uninsured-deposit coefficients from the main sample and its two failed-bank robustness samples. */
export function parseRegressionComparisons(text) {
  const comparisons = [
    ["R1 BHAR on uninsured share + HTM loss/equity (main sample: without SVB)", "Main: excluding SVB"],
    ["R6 R1 including SVB (the earlier baseline)", "Including SVB"],
    ["R3 R1 also without Signature (no imputed -100% returns)", "Excluding SVB and Signature"],
  ];
  const samples = new Map(comparisons);
  const expectedFormula = "bhar_0_2 ~ uninsured_dep_share + htm_loss_to_equity + log_assets";
  const [header = [], ...records] = csvRecords(text);
  const headers = header.map((value) => value.trim());
  const column = new Map(headers.map((name, index) => [name, index]));
  const requiredColumns = ["spec", "formula", "variable", "coef", "se", "t", "p", "n", "r2"];
  const missing = requiredColumns.filter((name) => !column.has(name));
  if (missing.length) throw new Error(`Missing regression CSV columns: ${missing.join(", ")}.`);
  if (column.size !== headers.length) throw new Error("The regression CSV has duplicate column names.");

  const selected = new Map();
  records.forEach((record, index) => {
    const label = `Regression CSV record ${index + 2}`;
    if (record.length !== headers.length) {
      throw new Error(`${label} has ${record.length} columns; expected ${headers.length}.`);
    }
    const read = (name) => record[column.get(name)];
    const spec = read("spec");
    if (!samples.has(spec) || read("variable") !== "uninsured_dep_share") return;
    if (selected.has(spec)) throw new Error(`${label} repeats the uninsured-deposit coefficient for ${spec}.`);
    if (read("formula").trim() !== expectedFormula) {
      throw new Error(`${label} has an incompatible formula for ${spec}.`);
    }

    const row = { sample: samples.get(spec), spec };
    for (const name of ["n", "coef", "se"]) {
      const value = read(name).trim();
      const number = Number(value);
      if (!decimal.test(value) || !Number.isFinite(number)) {
        throw new Error(`${label} has an invalid number in ${name}.`);
      }
      if (name === "se" && number < 0) throw new Error(`${label} has a negative standard error.`);
      if (name === "n" && (!Number.isSafeInteger(number) || number <= 0)) {
        throw new Error(`${label} needs a positive integer sample size.`);
      }
      row[name] = number;
    }
    selected.set(spec, row);
  });

  const absent = comparisons.filter(([spec]) => !selected.has(spec)).map(([spec]) => spec);
  if (absent.length) throw new Error(`Missing uninsured-deposit regression rows: ${absent.join("; ")}.`);
  return comparisons.map(([spec]) => selected.get(spec));
}

/** Read R1–R10 uninsured-deposit coefficients and approximate 95% intervals from regression outputs. */
export function parseCoefficientComparisons(text) {
  const targets = new Map(Array.from({ length: 10 }, (_, index) => {
    const id = `R${index + 1}`;
    return [id, id === "R8" || id === "R9" ? "uninsured_dep_share_w" : "uninsured_dep_share"];
  }));
  const [header = [], ...records] = csvRecords(text);
  const headers = header.map((value) => value.trim());
  const column = new Map(headers.map((name, index) => [name, index]));
  const required = ["spec", "formula", "variable", "coef", "se", "t", "p", "n", "r2"];
  const missing = required.filter((name) => !column.has(name));
  if (missing.length) throw new Error(`Missing regression CSV columns: ${missing.join(", ")}.`);
  if (column.size !== headers.length) throw new Error("The regression CSV has duplicate column names.");

  const selected = new Map();
  records.forEach((record, index) => {
    const label = `Regression CSV record ${index + 2}`;
    if (record.length !== headers.length) {
      throw new Error(`${label} has ${record.length} columns; expected ${headers.length}.`);
    }
    const read = (name) => record[column.get(name)].trim();
    const spec = read("spec");
    const id = spec.match(/^(R(?:10|[1-9]))\s+\S/)?.[1];
    const variable = read("variable");
    if (!targets.has(id) || variable !== targets.get(id)) return;
    if (selected.has(id)) throw new Error(`${label} repeats the uninsured-deposit coefficient for ${id}.`);

    const row = { id, spec, variable };
    for (const name of ["n", "coef", "se"]) {
      const value = read(name);
      const number = Number(value);
      if (!decimal.test(value) || !Number.isFinite(number)) {
        throw new Error(`${label} has an invalid number in ${name}.`);
      }
      if (name === "se" && number < 0) throw new Error(`${label} has a negative standard error.`);
      if (name === "n" && (!Number.isSafeInteger(number) || number <= 0)) {
        throw new Error(`${label} needs a positive integer sample size.`);
      }
      row[name] = number;
    }
    row.low = row.coef - 1.96 * row.se;
    row.high = row.coef + 1.96 * row.se;
    if (!Number.isFinite(row.low) || !Number.isFinite(row.high)) {
      throw new Error(`${label} has an interval outside the finite numeric range.`);
    }
    selected.set(id, row);
  });

  const absent = [...targets.keys()].filter((id) => !selected.has(id));
  if (absent.length) throw new Error(`Missing uninsured-deposit regression rows: ${absent.join(", ")}.`);
  return [...targets.keys()].map((id) => selected.get(id));
}

/** Read a CSV into objects keyed by its header, checking that the named columns exist. */
function readTable(text, required, what) {
  const [header = [], ...records] = csvRecords(text);
  const headers = header.map((value) => value.trim());
  const missing = required.filter((name) => !headers.includes(name));
  if (missing.length) throw new Error(`Missing ${what} columns: ${missing.join(", ")}.`);
  return records.map((record, index) => {
    if (record.length !== headers.length) {
      throw new Error(`${what} record ${index + 2} has ${record.length} columns; expected ${headers.length}.`);
    }
    return Object.fromEntries(headers.map((name, i) => [name, record[i]]));
  });
}

const toNumber = (value) => {
  const text = (value ?? "").trim();
  if (text === "") return null;
  if (!decimal.test(text)) throw new Error(`Invalid number "${text}" in screen output.`);
  return Number(text);
};
const toBool = (value) => {
  const text = (value ?? "").trim().toLowerCase();
  return text === "true" ? true : text === "false" ? false : null;
};

/** Step 8's per-bank screen output, keyed by RSSD ID. */
export function parseScreenCsv(text) {
  const rows = readTable(text, ["rssd_id", "rank", "score", "flag_top10", "fdic_failure", "failed_before_window",
    "post_bhr", "post_missing_reason"], "Screen");
  return new Map(rows.map((row) => [row.rssd_id.trim(), {
    rank: toNumber(row.rank), score: toNumber(row.score), flag_top10: toBool(row.flag_top10),
    fdic_failure: toBool(row.fdic_failure), failed_before_window: toBool(row.failed_before_window),
    fdic_fail_date: (row.fdic_fail_date ?? "").trim() || null,
    post_bhr: toNumber(row.post_bhr), post_missing_reason: (row.post_missing_reason ?? "").trim(),
  }]));
}

/** Step 8's recall and precision table. */
export function parseScorecardCsv(text) {
  return readTable(text, ["outcome", "label", "cutoff", "events", "flagged", "hits", "recall", "precision",
    "base_rate", "missing"], "Scorecard").map((row) => ({
    outcome: row.outcome, label: row.label, cutoff: toNumber(row.cutoff), events: toNumber(row.events),
    flagged: toNumber(row.flagged), hits: toNumber(row.hits), recall: toNumber(row.recall),
    precision: toNumber(row.precision), base_rate: toNumber(row.base_rate), missing: toNumber(row.missing),
  }));
}

/** Step 9's comparison of Dec 2022 with the latest quarter (one row per date, oldest first). */
export function parseTodaySummary(text) {
  const numbers = ["banks_ranked", "median_uninsured_share", "p90_uninsured_share", "median_sec_loss_to_equity",
    "p90_sec_loss_to_equity", "at_or_above_frc_both", "at_or_above_frc_uninsured", "at_or_above_frc_sec_loss",
    "frc_uninsured_benchmark", "frc_sec_loss_benchmark"];
  const rows = readTable(text, ["report_date", "date", ...numbers], "Today summary").map((row) => {
    const out = { report_date: row.report_date.trim(), date: row.date.trim() };
    for (const name of numbers) out[name] = toNumber(row[name]);
    return out;
  });
  if (rows.length !== 2 || !/^\d{8}$/.test(rows[1].report_date)) {
    throw new Error("The today summary needs two rows: Dec 2022 and the latest report date.");
  }
  return rows;
}

/** Step 9's ranked list for the latest quarter. */
export function parseTodayScreen(text) {
  return readTable(text, ["rank", "ticker", "name", "total_assets_bn", "uninsured_dep_share", "sec_loss_to_equity",
    "flag_top10"], "Today's screen").map((row) => ({
    rank: toNumber(row.rank), ticker: row.ticker.trim(), name: row.name.trim(),
    total_assets_bn: toNumber(row.total_assets_bn), uninsured_dep_share: toNumber(row.uninsured_dep_share),
    sec_loss_to_equity: toNumber(row.sec_loss_to_equity), flag_top10: toBool(row.flag_top10),
  }));
}
