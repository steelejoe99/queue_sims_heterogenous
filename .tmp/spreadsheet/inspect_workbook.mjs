import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const sourcePath = "/Users/jste924/Downloads/housing_simulation_parameter_requirements.xlsx";
const previewPath = "/private/tmp/housing_parameter_requirements_original.png";

const input = await FileBlob.load(sourcePath);
const workbook = await SpreadsheetFile.importXlsx(input);

const summary = await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 12000,
  tableMaxRows: 16,
  tableMaxCols: 8,
  tableMaxCellChars: 100,
});
console.log(summary.ndjson);

const image = await workbook.render({
  sheetName: "Study 1 Inputs",
  range: "A1:G30",
  scale: 1.5,
  format: "png",
});
await fs.writeFile(previewPath, new Uint8Array(await image.arrayBuffer()));
console.log(`PREVIEW=${previewPath}`);
