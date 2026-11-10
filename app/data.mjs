const textColumns = ["ticker", "entity_name", "call_report_date", "car_note"];
const numericColumns = [
  "total_assets_bn",
  "uninsured_dep_share",
  "sec_loss_to_equity",
  "htm_loss_to_equity",
  "car_0_2",
];
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

function isDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isFinite(date.valueOf()) && date.toISOString().slice(0, 10) === value;
}

/** Read one dashboard output row per ticker. Keep missing numbers distinct from zero. */
export function parseDashboardCsv(text) {
  const [header = [], ...records] = csvRecords(text);
  const headers = header.map((value) => value.trim());
  const column = new Map(headers.map((name, index) => [name, index]));
  const requiredColumns = [...textColumns, ...numericColumns];
  const missing = requiredColumns.filter((name) => !column.has(name));
  if (missing.length) throw new Error(`Missing CSV columns: ${missing.join(", ")}.`);
  if (column.size !== headers.length) throw new Error("The CSV has duplicate column names.");
  if (!records.length) throw new Error("The CSV has no bank rows.");

  const tickers = new Set();
  return records.map((record, index) => {
    const label = `CSV record ${index + 2}`;
    if (record.length !== headers.length) {
      throw new Error(`${label} has ${record.length} columns; expected ${headers.length}.`);
    }

    const read = (name) => record[column.get(name)].trim();
    const row = Object.fromEntries(textColumns.map((name) => [name, read(name)]));
    if (!row.ticker || !row.entity_name) throw new Error(`${label} is missing a ticker or bank name.`);
    if (!isDate(row.call_report_date)) throw new Error(`${label} needs a valid YYYY-MM-DD call report date.`);

    const key = row.ticker.toUpperCase();
    if (tickers.has(key)) throw new Error(`${label} repeats ticker ${row.ticker}.`);
    tickers.add(key);

    for (const name of numericColumns) {
      const value = read(name);
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
    return row;
  });
}
