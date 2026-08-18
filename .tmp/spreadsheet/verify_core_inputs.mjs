import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const workbookPath = "/Users/jste924/Documents/Python scripts/RA work/queue_sims_heterogenous/outputs/housing_simulation_core_inputs.xlsx";
const previewPath = "/private/tmp/housing_simulation_core_inputs.png";

const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(workbookPath));
const values = await workbook.inspect({
  kind: "table",
  range: "Core Study Inputs!A1:E16",
  include: "values,formulas",
  tableMaxRows: 20,
  tableMaxCols: 6,
  maxChars: 10000,
});
console.log(values.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 50 },
  summary: "formula error scan",
});
console.log(errors.ndjson);

const image = await workbook.render({
  sheetName: "Core Study Inputs",
  range: "A1:E16",
  scale: 1.5,
  format: "png",
});
await fs.writeFile(previewPath, new Uint8Array(await image.arrayBuffer()));
console.log(`PREVIEW=${previewPath}`);
