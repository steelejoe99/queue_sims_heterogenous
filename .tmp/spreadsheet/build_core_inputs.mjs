import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "/Users/jste924/Documents/Python scripts/RA work/queue_sims_heterogenous/outputs";
const outputPath = `${outputDir}/housing_simulation_core_inputs.xlsx`;

const rows = [
  [1, "True chronic outcome", "Long-term homelessness", "Available", "Keep the 90-365 day outcome definition."],
  [2, "Annual applicants and arrival timing", "200 per year; annual batches", "Data needed", "Number assessed and their assessment dates."],
  [3, "True chronic prevalence", "40%", "Data needed", "Observed prevalence of the 90-365 day outcome."],
  [4, "Housing supply and release timing", "50-150 placements/year; annual releases", "Data needed", "Annual placements and dates units become available."],
  [5, "Classifier sensitivity and specificity", "s(q) = q + 0.05; r(q) = q - 0.05", "Data needed", "Performance of HAST and the current tool at the chosen threshold."],
  [6, "Abandonment definition and patience", "Class-specific lognormal patience", "Data needed", "Exit definition and assessment-to-exit times."],
  [7, "Initial backlog and available stock", "0 people; 0 units", "Data needed", "People already waiting and housing available at the start."],
  [8, "Eligibility delay", "1 year", "Assumption", "Actual time before housing can be allocated."],
  [9, "HAST classification threshold", "Proposed HAST >= 8", "Decision needed", "Confirm the threshold used for priority."],
  [10, "Allocation policy", "Assigned chronic first; FCFS within class", "Policy choice", "Confirm the operational ranking rule."],
  [11, "Simulation horizon and replications", "50 years; 3 seeds", "Analysis choice", "Use a policy-relevant horizon and more seeds for final estimates."],
];

const workbook = Workbook.create();
const sheet = workbook.worksheets.add("Core Study Inputs");
sheet.showGridLines = false;

sheet.mergeCells("A1:E1");
sheet.getRange("A1").values = [["Core Inputs for the Housing Allocation Simulation"]];
sheet.getRange("A1:E1").format = {
  fill: "#173F5F",
  font: { bold: true, color: "#FFFFFF", size: 16 },
  horizontalAlignment: "left",
  verticalAlignment: "center",
};
sheet.getRange("A1:E1").format.rowHeight = 30;

sheet.mergeCells("A2:E2");
sheet.getRange("A2").values = [["Study 1: classifier quality and housing supply. Start with priorities 1-6 for a credible first calibration."]];
sheet.getRange("A2:E2").format = {
  fill: "#EAF2F8",
  font: { color: "#355C7D", italic: true },
  horizontalAlignment: "left",
  verticalAlignment: "center",
  wrapText: true,
};
sheet.getRange("A2:E2").format.rowHeight = 30;

sheet.getRange("A4:E4").values = [[
  "Priority",
  "Core input",
  "Current study setting",
  "Evidence status",
  "What is needed",
]];
sheet.getRange("A4:E4").format = {
  fill: "#2F75B5",
  font: { bold: true, color: "#FFFFFF" },
  horizontalAlignment: "center",
  verticalAlignment: "center",
  wrapText: true,
  borders: { preset: "outside", style: "thin", color: "#2F75B5" },
};
sheet.getRange("A4:E4").format.rowHeight = 26;

sheet.getRange("A5:E15").values = rows;
sheet.getRange("A5:E15").format = {
  verticalAlignment: "center",
  wrapText: true,
  borders: { insideHorizontal: { style: "thin", color: "#D9E2F3" } },
};
sheet.getRange("A5:A15").format = {
  horizontalAlignment: "center",
  verticalAlignment: "center",
  font: { bold: true, color: "#173F5F" },
};
sheet.getRange("B5:B15").format = { font: { bold: true }, verticalAlignment: "center", wrapText: true };
sheet.getRange("C5:C15").format = { verticalAlignment: "center", wrapText: true };
sheet.getRange("D5:D15").format = { horizontalAlignment: "center", verticalAlignment: "center", font: { bold: true }, wrapText: true };
sheet.getRange("E5:E15").format = { verticalAlignment: "center", wrapText: true };
sheet.getRange("A5:E15").format.rowHeight = 34;

const statusColors = {
  "Available": "#DDEBF7",
  "Data needed": "#FCE4D6",
  "Assumption": "#FFF2CC",
  "Decision needed": "#FFF2CC",
  "Policy choice": "#E2F0D9",
  "Analysis choice": "#EDEDED",
};
for (let row = 0; row < rows.length; row += 1) {
  const cell = sheet.getRange(`D${row + 5}`);
  cell.format.fill = statusColors[rows[row][3]];
}

sheet.getRange("A16:E16").merge();
sheet.getRange("A16").values = [["The most urgent empirical inputs are annual entrants, housing placements, classifier performance, and exit timing."]];
sheet.getRange("A16:E16").format = {
  fill: "#F3F6F9",
  font: { italic: true, color: "#355C7D" },
  horizontalAlignment: "left",
  verticalAlignment: "center",
  wrapText: true,
  borders: { preset: "outside", style: "thin", color: "#D9E2F3" },
};
sheet.getRange("A16:E16").format.rowHeight = 26;

sheet.getRange("A1:A16").format.columnWidth = 11;
sheet.getRange("B1:B16").format.columnWidth = 30;
sheet.getRange("C1:C16").format.columnWidth = 31;
sheet.getRange("D1:D16").format.columnWidth = 16;
sheet.getRange("E1:E16").format.columnWidth = 42;
sheet.freezePanes.freezeRows(4);

await fs.mkdir(outputDir, { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(outputPath);
