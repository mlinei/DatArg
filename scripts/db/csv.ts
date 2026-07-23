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

function escapeCell(value: unknown) {
  const text = String(value ?? '');
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export function rowsToCsv(rows: CsvRow[]) {
  const body = rows.map(row => CSV_COLUMNS.map(column => escapeCell(row[column])).join(','));
  return `${CSV_COLUMNS.join(',')}\n${body.join('\n')}\n`;
}
