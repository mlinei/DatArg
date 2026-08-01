export const CSV_COLUMNS = [
  'series_id',
  'period',
  'frequency',
  'value',
  'unit',
  'status',
  'source_id',
  'source_url',
  'source_sha256',
  'retrieved_at',
] as const;

export type CsvRow = Record<(typeof CSV_COLUMNS)[number], string>;

export const MATURITY_CSV_COLUMNS = [
  'series_id',
  'snapshot_date',
  'period',
  'frequency',
  'service_type',
  'category',
  'detail_level',
  'source_row',
  'instrument',
  'value',
  'unit',
  'status',
  'source_id',
  'source_url',
  'source_sha256',
  'retrieved_at',
] as const;

export type MaturityCsvRow = Record<(typeof MATURITY_CSV_COLUMNS)[number], string>;

export const YIELD_CURVE_CSV_COLUMNS = [
  'snapshot_date', 'ticker', 'instrument_name', 'curve_type', 'instrument_type',
  'settlement_date', 'maturity_date', 'days_to_maturity', 'price', 'annual_yield',
  'monthly_yield', 'duration_years', 'volume', 'status', 'source_id', 'source_url',
  'source_sha256', 'retrieved_at',
] as const;
export type YieldCurveCsvRow = Record<(typeof YIELD_CURVE_CSV_COLUMNS)[number], string>;

function parseLine(line: string) {
  const cells: string[] = [];
  let cell = '';
  let quoted = false;

  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];
    if (character === '"') {
      if (quoted && line[index + 1] === '"') {
        cell += '"';
        index += 1;
      } else {
        quoted = !quoted;
      }
    } else if (character === ',' && !quoted) {
      cells.push(cell);
      cell = '';
    } else {
      cell += character;
    }
  }
  cells.push(cell);
  return cells;
}

export function parseCsv(text: string): CsvRow[] {
  const lines = text.replace(/^\uFEFF/, '').trim().split(/\r?\n/);
  const headers = parseLine(lines.shift() || '');
  if (headers.join(',') !== CSV_COLUMNS.join(',')) {
    throw new Error(`Cabecera CSV inesperada: ${headers.join(',')}`);
  }

  return lines.filter(Boolean).map((line, rowIndex) => {
    const cells = parseLine(line);
    if (cells.length !== CSV_COLUMNS.length) {
      throw new Error(`Fila ${rowIndex + 2}: se esperaban ${CSV_COLUMNS.length} columnas y hay ${cells.length}`);
    }
    return Object.fromEntries(CSV_COLUMNS.map((column, index) => [column, cells[index]])) as CsvRow;
  });
}

export function parseMaturityCsv(text: string): MaturityCsvRow[] {
  const lines = text.replace(/^\uFEFF/, '').trim().split(/\r?\n/);
  const headers = parseLine(lines.shift() || '');
  if (headers.join(',') !== MATURITY_CSV_COLUMNS.join(',')) {
    throw new Error(`Cabecera de vencimientos inesperada: ${headers.join(',')}`);
  }
  return lines.filter(Boolean).map((line, rowIndex) => {
    const cells = parseLine(line);
    if (cells.length !== MATURITY_CSV_COLUMNS.length) {
      throw new Error(`Fila ${rowIndex + 2}: se esperaban ${MATURITY_CSV_COLUMNS.length} columnas y hay ${cells.length}`);
    }
    return Object.fromEntries(MATURITY_CSV_COLUMNS.map((column, index) => [column, cells[index]])) as MaturityCsvRow;
  });
}

export function parseYieldCurveCsv(text: string): YieldCurveCsvRow[] {
  const lines = text.replace(/^\uFEFF/, '').trim().split(/\r?\n/);
  const headers = parseLine(lines.shift() || '');
  if (headers.join(',') !== YIELD_CURVE_CSV_COLUMNS.join(',')) {
    throw new Error(`Cabecera de curvas inesperada: ${headers.join(',')}`);
  }
  return lines.filter(Boolean).map((line, rowIndex) => {
    const cells = parseLine(line);
    if (cells.length !== YIELD_CURVE_CSV_COLUMNS.length) throw new Error(`Fila ${rowIndex + 2}: curva incompleta`);
    return Object.fromEntries(YIELD_CURVE_CSV_COLUMNS.map((column, index) => [column, cells[index]])) as YieldCurveCsvRow;
  });
}

function escapeCell(value: unknown) {
  const text = String(value ?? '');
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export function rowsToCsv(rows: CsvRow[]) {
  const body = rows.map(row => CSV_COLUMNS.map(column => escapeCell(row[column])).join(','));
  return `${CSV_COLUMNS.join(',')}\n${body.join('\n')}\n`;
}

export function maturityRowsToCsv(rows: MaturityCsvRow[]) {
  const body = rows.map(row => MATURITY_CSV_COLUMNS.map(column => escapeCell(row[column])).join(','));
  return `${MATURITY_CSV_COLUMNS.join(',')}\n${body.join('\n')}\n`;
}

export function yieldCurveRowsToCsv(rows: YieldCurveCsvRow[]) {
  const body = rows.map(row => YIELD_CURVE_CSV_COLUMNS.map(column => escapeCell(row[column])).join(','));
  return `${YIELD_CURVE_CSV_COLUMNS.join(',')}\n${body.join('\n')}\n`;
}
