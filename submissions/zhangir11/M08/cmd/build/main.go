package main

import (
	"encoding/csv"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"

	"github.com/xuri/excelize/v2"
)

type planRow struct {
	Category string
	Amount   float64
}

type actualRow struct {
	ID, Date, Category string
	Amount             float64
}

func fail(err error) {
	if err != nil {
		panic(err)
	}
}

func ptr[T any](value T) *T { return &value }

func rootDir() string {
	_, file, _, ok := runtime.Caller(0)
	if !ok {
		panic("cannot locate source file")
	}
	return filepath.Clean(filepath.Join(filepath.Dir(file), "..", ".."))
}

func readCSV(path string) [][]string {
	file, err := os.Open(path)
	fail(err)
	defer file.Close()
	rows, err := csv.NewReader(file).ReadAll()
	fail(err)
	return rows
}

func readInputs(root string) ([]planRow, []actualRow, []string, map[string]float64, map[string]float64) {
	var plans []planRow
	var actuals []actualRow
	categories := make([]string, 0)
	seen := map[string]bool{}
	planByCategory := map[string]float64{}
	actualByCategory := map[string]float64{}

	for _, row := range readCSV(filepath.Join(root, "source", "plan.csv"))[1:] {
		amount, err := strconv.ParseFloat(row[1], 64)
		fail(err)
		plans = append(plans, planRow{row[0], amount})
		planByCategory[row[0]] = amount
		if !seen[row[0]] {
			seen[row[0]] = true
			categories = append(categories, row[0])
		}
	}
	for _, row := range readCSV(filepath.Join(root, "source", "actual.csv"))[1:] {
		amount, err := strconv.ParseFloat(row[3], 64)
		fail(err)
		actuals = append(actuals, actualRow{row[0], row[1], row[2], amount})
		actualByCategory[row[2]] += amount
		if !seen[row[2]] {
			seen[row[2]] = true
			categories = append(categories, row[2])
		}
	}
	return plans, actuals, categories, planByCategory, actualByCategory
}

func style(f *excelize.File, value *excelize.Style) int {
	id, err := f.NewStyle(value)
	fail(err)
	return id
}

func set(f *excelize.File, sheet, cell string, value any, styleID int) {
	fail(f.SetCellValue(sheet, cell, value))
	if styleID != 0 {
		fail(f.SetCellStyle(sheet, cell, cell, styleID))
	}
}

func main() {
	root := rootDir()
	plans, actuals, categories, planByCategory, actualByCategory := readInputs(root)
	f := excelize.NewFile()
	defer f.Close()
	fail(f.SetSheetName("Sheet1", "План-факт"))
	_, err := f.NewSheet("План")
	fail(err)
	_, err = f.NewSheet("Факт")
	fail(err)
	fail(f.SetDocProps(&excelize.DocProperties{
		Title: "План-факт бюджета", Subject: "M08 — редактируемая модель",
		Creator: "zhangir11", Description: "Источники: source/plan.csv и source/actual.csv",
	}))
	fail(f.SetCalcProps(&excelize.CalcPropsOptions{
		CalcMode: ptr("auto"), FullCalcOnLoad: ptr(true), CalcOnSave: ptr(true), ForceFullCalc: ptr(true),
	}))

	border := []excelize.Border{{Type: "left", Color: "000000", Style: 1}, {Type: "right", Color: "000000", Style: 1}, {Type: "top", Color: "000000", Style: 1}, {Type: "bottom", Color: "000000", Style: 1}}
	titleStyle := style(f, &excelize.Style{Font: &excelize.Font{Bold: true, Size: 20, Color: "17365D"}})
	subtitleStyle := style(f, &excelize.Style{Font: &excelize.Font{Size: 10, Color: "666666"}})
	headerStyle := style(f, &excelize.Style{Font: &excelize.Font{Bold: true, Color: "FFFFFF"}, Fill: excelize.Fill{Type: "pattern", Color: []string{"17365D"}, Pattern: 1}, Border: border, Alignment: &excelize.Alignment{Horizontal: "center", Vertical: "center", WrapText: true}})
	textStyle := style(f, &excelize.Style{Border: border})
	moneyStyle := style(f, &excelize.Style{Border: border, CustomNumFmt: ptr(`#,##0 "KZT"`)})
	percentStyle := style(f, &excelize.Style{Border: border, NumFmt: 10})
	totalTextStyle := style(f, &excelize.Style{Font: &excelize.Font{Bold: true}, Fill: excelize.Fill{Type: "pattern", Color: []string{"D9EAD3"}, Pattern: 1}, Border: border})
	totalMoneyStyle := style(f, &excelize.Style{Font: &excelize.Font{Bold: true}, Fill: excelize.Fill{Type: "pattern", Color: []string{"D9EAD3"}, Pattern: 1}, Border: border, CustomNumFmt: ptr(`#,##0 "KZT"`)})
	totalPercentStyle := style(f, &excelize.Style{Font: &excelize.Font{Bold: true}, Fill: excelize.Fill{Type: "pattern", Color: []string{"D9EAD3"}, Pattern: 1}, Border: border, NumFmt: 10})
	inputTextStyle := style(f, &excelize.Style{Fill: excelize.Fill{Type: "pattern", Color: []string{"FFF2CC"}, Pattern: 1}, Border: border})
	inputMoneyStyle := style(f, &excelize.Style{Fill: excelize.Fill{Type: "pattern", Color: []string{"FFF2CC"}, Pattern: 1}, Border: border, CustomNumFmt: ptr(`#,##0 "KZT"`)})
	noteStyle := style(f, &excelize.Style{Font: &excelize.Font{Italic: true, Size: 9, Color: "666666"}, Alignment: &excelize.Alignment{WrapText: true}})
	warningStyle, err := f.NewConditionalStyle(&excelize.Style{Font: &excelize.Font{Color: "9C0006"}, Fill: excelize.Fill{Type: "pattern", Color: []string{"F4CCCC"}, Pattern: 1}})
	fail(err)

	summary := "План-факт"
	fail(f.MergeCell(summary, "A1", "E1"))
	fail(f.MergeCell(summary, "A2", "E2"))
	set(f, summary, "A1", "План-факт бюджета", titleStyle)
	set(f, summary, "A2", "Синие ячейки — формулы; жёлтые ячейки на листах «План» и «Факт» редактируются.", subtitleStyle)
	for idx, value := range []string{"Категория", "План, KZT", "Факт, KZT", "Отклонение, KZT", "Отклонение, %"} {
		cell, _ := excelize.CoordinatesToCellName(idx+1, 4)
		set(f, summary, cell, value, headerStyle)
	}
	for idx, category := range categories {
		row := idx + 5
		set(f, summary, fmt.Sprintf("A%d", row), category, textStyle)
		formulas := map[string]string{
			"B": fmt.Sprintf("SUMIF('План'!$A$2:$A$1000,A%d,'План'!$B$2:$B$1000)", row),
			"C": fmt.Sprintf("SUMIF('Факт'!$C$2:$C$1000,A%d,'Факт'!$D$2:$D$1000)", row),
			"D": fmt.Sprintf("C%d-B%d", row, row),
			"E": fmt.Sprintf("IF(B%d=0,\"нет базы\",D%d/B%d)", row, row, row),
		}
		for _, col := range []string{"B", "C", "D", "E"} {
			cell := fmt.Sprintf("%s%d", col, row)
			fail(f.SetCellFormula(summary, cell, formulas[col]))
			cellStyle := moneyStyle
			if col == "E" {
				cellStyle = percentStyle
			}
			fail(f.SetCellStyle(summary, cell, cell, cellStyle))
		}
	}
	totalRow := len(categories) + 5
	set(f, summary, fmt.Sprintf("A%d", totalRow), "ИТОГО", totalTextStyle)
	for col, formula := range map[string]string{
		"B": fmt.Sprintf("SUM(B5:B%d)", totalRow-1), "C": fmt.Sprintf("SUM(C5:C%d)", totalRow-1),
		"D": fmt.Sprintf("C%d-B%d", totalRow, totalRow), "E": fmt.Sprintf("IF(B%d=0,\"нет базы\",D%d/B%d)", totalRow, totalRow, totalRow),
	} {
		cell := fmt.Sprintf("%s%d", col, totalRow)
		fail(f.SetCellFormula(summary, cell, formula))
		cellStyle := totalMoneyStyle
		if col == "E" {
			cellStyle = totalPercentStyle
		}
		fail(f.SetCellStyle(summary, cell, cell, cellStyle))
	}
	lastCategoryRow := totalRow - 1
	fail(f.SetConditionalFormat(summary, fmt.Sprintf("A5:E%d", lastCategoryRow), []excelize.ConditionalFormatOptions{{Type: "formula", Criteria: "$D5>0", Format: &warningStyle}}))
	set(f, summary, fmt.Sprintf("A%d", totalRow+2), "Красное выделение: факт выше плана (отклонение > 0).", noteStyle)
	fail(f.SetColWidth(summary, "A", "A", 20))
	fail(f.SetColWidth(summary, "B", "D", 18))
	fail(f.SetColWidth(summary, "E", "E", 16))
	fail(f.SetRowHeight(summary, 1, 30))
	fail(f.SetRowHeight(summary, 4, 32))
	fail(f.SetSheetView(summary, 0, &excelize.ViewOptions{ShowGridLines: ptr(false)}))
	fail(f.SetPanes(summary, &excelize.Panes{Freeze: true, Split: false, XSplit: 1, YSplit: 4, TopLeftCell: "B5", ActivePane: "bottomRight"}))
	fail(f.AutoFilter(summary, fmt.Sprintf("A4:E%d", lastCategoryRow), nil))
	fail(f.SetPageLayout(summary, &excelize.PageLayoutOptions{Orientation: ptr("landscape"), FitToWidth: ptr(1), FitToHeight: ptr(1)}))
	fail(f.SetSheetProps(summary, &excelize.SheetPropsOptions{FitToPage: ptr(true)}))
	// Extra print-area padding keeps LibreOffice from clipping the chart edge.
	fail(f.SetDefinedName(&excelize.DefinedName{Name: "_xlnm.Print_Area", RefersTo: "'План-факт'!$A$1:$R$20", Scope: summary}))

	fail(f.AddChart(summary, "G4", &excelize.Chart{
		Type: excelize.Bar,
		Series: []excelize.ChartSeries{
			{Name: "'План-факт'!$B$4", Categories: fmt.Sprintf("'План-факт'!$A$5:$A$%d", lastCategoryRow), Values: fmt.Sprintf("'План-факт'!$B$5:$B$%d", lastCategoryRow), Fill: excelize.Fill{Type: "solid", Color: []string{"4472C4"}}},
			{Name: "'План-факт'!$C$4", Categories: fmt.Sprintf("'План-факт'!$A$5:$A$%d", lastCategoryRow), Values: fmt.Sprintf("'План-факт'!$C$5:$C$%d", lastCategoryRow), Fill: excelize.Fill{Type: "solid", Color: []string{"ED7D31"}}},
		},
		Dimension: excelize.ChartDimension{Width: 720, Height: 390},
		Title:     []excelize.RichTextRun{{Text: "План и факт по категориям"}},
		XAxis:     excelize.ChartAxis{Title: []excelize.RichTextRun{{Text: "Категория"}}},
		YAxis:     excelize.ChartAxis{Title: []excelize.RichTextRun{{Text: "Сумма, KZT"}}, MajorGridLines: true},
		Legend:    excelize.ChartLegend{Position: "right"}, ShowBlanksAs: "zero",
	}))

	for _, sheet := range []string{"План", "Факт"} {
		fail(f.SetSheetView(sheet, 0, &excelize.ViewOptions{ShowGridLines: ptr(false)}))
		fail(f.SetPanes(sheet, &excelize.Panes{Freeze: true, YSplit: 1, TopLeftCell: "A2", ActivePane: "bottomLeft"}))
	}
	set(f, "План", "A1", "category", headerStyle)
	set(f, "План", "B1", "plan_KZT", headerStyle)
	for idx, row := range plans {
		set(f, "План", fmt.Sprintf("A%d", idx+2), row.Category, inputTextStyle)
		set(f, "План", fmt.Sprintf("B%d", idx+2), row.Amount, inputMoneyStyle)
	}
	fail(f.SetColWidth("План", "A", "A", 24))
	fail(f.SetColWidth("План", "B", "B", 18))
	fail(f.AddTable("План", &excelize.Table{Range: fmt.Sprintf("A1:B%d", len(plans)+1), Name: "PlanData", StyleName: "TableStyleMedium2"}))
	planValidation := excelize.NewDataValidation(false)
	planValidation.Sqref = "B2:B1000"
	fail(planValidation.SetRange(0, 0, excelize.DataValidationTypeDecimal, excelize.DataValidationOperatorGreaterThanOrEqual))
	planValidation.SetInput("План, KZT", "Введите неотрицательную сумму.")
	planValidation.SetError(excelize.DataValidationErrorStyleStop, "Неверная сумма", "План должен быть числом от 0 и выше.")
	fail(f.AddDataValidation("План", planValidation))

	for idx, value := range []string{"id", "date", "category", "amount_KZT"} {
		cell, _ := excelize.CoordinatesToCellName(idx+1, 1)
		set(f, "Факт", cell, value, headerStyle)
	}
	for idx, row := range actuals {
		r := idx + 2
		set(f, "Факт", fmt.Sprintf("A%d", r), row.ID, inputTextStyle)
		set(f, "Факт", fmt.Sprintf("B%d", r), row.Date, inputTextStyle)
		set(f, "Факт", fmt.Sprintf("C%d", r), row.Category, inputTextStyle)
		set(f, "Факт", fmt.Sprintf("D%d", r), row.Amount, inputMoneyStyle)
	}
	fail(f.SetColWidth("Факт", "A", "A", 12))
	fail(f.SetColWidth("Факт", "B", "B", 14))
	fail(f.SetColWidth("Факт", "C", "C", 24))
	fail(f.SetColWidth("Факт", "D", "D", 18))
	fail(f.AddTable("Факт", &excelize.Table{Range: fmt.Sprintf("A1:D%d", len(actuals)+1), Name: "ActualData", StyleName: "TableStyleMedium2"}))
	actualValidation := excelize.NewDataValidation(false)
	actualValidation.Sqref = "D2:D1000"
	fail(actualValidation.SetRange(0, 0, excelize.DataValidationTypeDecimal, excelize.DataValidationOperatorGreaterThanOrEqual))
	actualValidation.SetError(excelize.DataValidationErrorStyleStop, "Неверная сумма", "Факт должен быть числом от 0 и выше.")
	fail(f.AddDataValidation("Факт", actualValidation))

	// Keep control arithmetic explicit in the Go build log.
	var totalPlan, totalActual float64
	for _, value := range planByCategory {
		totalPlan += value
	}
	for _, value := range actualByCategory {
		totalActual += value
	}

	tempDir, err := os.MkdirTemp("", "m08-go-build-")
	fail(err)
	defer os.RemoveAll(tempDir)
	draft := filepath.Join(tempDir, "budget_plan_fact.xlsx")
	fail(f.SaveAs(draft))
	output := filepath.Join(root, "budget_plan_fact.xlsx")
	fail(os.RemoveAll(output))
	command := exec.Command("soffice", "--headless", "--convert-to", "xlsx", "--outdir", root, draft)
	combined, err := command.CombinedOutput()
	if err != nil {
		panic(fmt.Errorf("LibreOffice recalculation failed: %w: %s", err, strings.TrimSpace(string(combined))))
	}
	if _, err := os.Stat(output); err != nil {
		panic(fmt.Errorf("LibreOffice did not create %s: %w", output, err))
	}
	fmt.Printf("Created %s with Go (plan %.0f, actual %.0f, delta %.0f KZT)\n", output, totalPlan, totalActual, totalActual-totalPlan)
}
