const textColumns = ["rssd_id", "ticker", "name"];
const numericColumns = [
  "total_assets_bn",
  "uninsured_dep_share",
  "sec_loss_to_equity",
  "htm_loss_to_equity",
  "bhar_0_2",
];
const booleanColumns = ["in_sample", "dlret_imputed", "has_fdic", "has_returns", "positive_equity"];
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

/** Read comparable uninsured-deposit coefficients from the three planned samples. */
export function parseRegressionComparisons(text) {
  const comparisons = [
    ["R1 BHAR on uninsured share + HTM loss/equity", "All banks"],
    ["R5 R1 without SVB (event trigger)", "Excluding SVB"],
    ["R3 R1 without SVB and Signature (imputed -100%)", "Excluding SVB and Signature"],
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
