package main

import (
	"archive/zip"
	"crypto/sha256"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"slices"
	"strconv"
	"strings"

	"github.com/xuri/excelize/v2"
)

func ptr[T any](value T) *T { return &value }

func rootDir() string {
	_, file, _, ok := runtime.Caller(0)
	if !ok {
		panic("cannot locate source file")
	}
	return filepath.Clean(filepath.Join(filepath.Dir(file), "..", ".."))
}

func must(err error) {
	if err != nil {
		panic(err)
	}
}

func check(condition bool, message string, results *[]string) {
	if !condition {
		panic("verification failed: " + message)
	}
	*results = append(*results, "PASS: "+message)
}

func digest(path string) string {
	data, err := os.ReadFile(path)
	must(err)
	return fmt.Sprintf("%x", sha256.Sum256(data))
}

func raw(f *excelize.File, sheet, cell string) string {
	value, err := f.GetCellValue(sheet, cell, excelize.Options{RawCellValue: true})
	must(err)
	return value
}

func number(f *excelize.File, sheet, cell string) float64 {
	value, err := strconv.ParseFloat(raw(f, sheet, cell), 64)
	must(err)
	return value
}

func formula(f *excelize.File, sheet, cell string) string {
	value, err := f.GetCellFormula(sheet, cell)
	must(err)
	return value
}

func copyFile(source, target string) {
	in, err := os.Open(source)
	must(err)
	defer in.Close()
	out, err := os.Create(target)
	must(err)
	_, err = io.Copy(out, in)
	must(err)
	must(out.Close())
}

func officeConvert(source, format, outDir string) string {
	must(os.MkdirAll(outDir, 0o755))
	command := exec.Command("soffice", "--headless", "--convert-to", format, "--outdir", outDir, source)
	output, err := command.CombinedOutput()
	if err != nil {
		panic(fmt.Errorf("LibreOffice conversion failed: %w: %s", err, strings.TrimSpace(string(output))))
	}
	ext := "." + strings.Split(format, ":")[0]
	result := filepath.Join(outDir, strings.TrimSuffix(filepath.Base(source), filepath.Ext(source))+ext)
	if _, err := os.Stat(result); err != nil {
		panic(fmt.Errorf("conversion output missing: %w", err))
	}
	return result
}

func chartXML(path string) (string, int) {
	reader, err := zip.OpenReader(path)
	must(err)
	defer reader.Close()
	var content strings.Builder
	count := 0
	for _, file := range reader.File {
		if strings.HasPrefix(file.Name, "xl/charts/chart") && strings.HasSuffix(file.Name, ".xml") {
			count++
			stream, err := file.Open()
			must(err)
			data, err := io.ReadAll(stream)
			must(err)
			must(stream.Close())
			content.Write(data)
		}
	}
	return content.String(), count
}

func main() {
	root := rootDir()
	workbook := filepath.Join(root, "budget_plan_fact.xlsx")
	evidence := filepath.Join(root, "evidence")
	results := []string{}
	expectedHashes := map[string]string{
		"plan.csv":      "c02fbb9f22b78317b675383323fa44e6a8ae27a9a7a1a2a3f4e51f1243d7a6cf",
		"actual.csv":    "09caa20994b0c23a7319cc383ab1ff5aa644fe2b93a0c963b8918c53b743fb6b",
		"rules.md":      "6a432a3c3fd0ba0884e1e1abaaf9cf37b60cfb4f2be6fd34be354825a3cd45ad",
		"expected.json": "de3e8493635f26b300cd1bc0fea6477748b4284d3f06fb10f356cfac8b70f8aa",
	}
	for name, want := range expectedHashes {
		check(digest(filepath.Join(root, "source", name)) == want, "source/"+name+" SHA-256 matches the issued material", &results)
	}
	_, err := os.Stat(workbook)
	check(err == nil, "editable XLSX exists", &results)
	f, err := excelize.OpenFile(workbook)
	must(err)
	defer f.Close()
	check(slices.Equal(f.GetSheetList(), []string{"План-факт", "План", "Факт"}), "workbook has summary and two editable input sheets", &results)
	calc, err := f.GetCalcProps()
	must(err)
	check(calc.CalcMode == nil || *calc.CalcMode == "auto", "automatic/default calculation mode is enabled", &results)

	categories := []string{raw(f, "План-факт", "A5"), raw(f, "План-факт", "A6"), raw(f, "План-факт", "A7"), raw(f, "План-факт", "A8")}
	check(slices.Equal(categories, []string{"Площадка", "Питание", "Печать", "Транспорт"}), "all union categories are present in source order", &results)
	plan := []float64{number(f, "План-факт", "B5"), number(f, "План-факт", "B6"), number(f, "План-факт", "B7"), number(f, "План-факт", "B8")}
	actual := []float64{number(f, "План-факт", "C5"), number(f, "План-факт", "C6"), number(f, "План-факт", "C7"), number(f, "План-факт", "C8")}
	deltas := []float64{number(f, "План-факт", "D5"), number(f, "План-факт", "D6"), number(f, "План-факт", "D7"), number(f, "План-факт", "D8")}
	check(slices.Equal(plan, []float64{140000, 70000, 10000, 0}), "category plan values are correct", &results)
	check(slices.Equal(actual, []float64{150000, 60000, 15000, 10000}), "category actual values are correctly aggregated", &results)
	check(slices.Equal(deltas, []float64{10000, -10000, 5000, 10000}), "category deltas equal fact minus plan", &results)
	check(number(f, "План-факт", "B9") == 220000 && number(f, "План-факт", "C9") == 235000 && number(f, "План-факт", "D9") == 15000, "total plan, actual, and delta are 220000 / 235000 / 15000 KZT", &results)
	check(raw(f, "План-факт", "E8") == "нет базы", "zero-plan category displays 'нет базы'", &results)
	check(strings.Contains(formula(f, "План-факт", "E8"), "B8=0") && strings.Contains(formula(f, "План-факт", "E8"), "нет базы"), "zero-plan formula guards division", &results)
	check(strings.Contains(formula(f, "План-факт", "B5"), "SUMIF") && strings.Contains(formula(f, "План-факт", "C5"), "SUMIF"), "summary plan and actual are formula-driven", &results)

	formats, err := f.GetConditionalFormats("План-факт")
	must(err)
	rules := formats["A5:E8"]
	check(len(rules) == 1, "conditional highlighting covers all category rows", &results)
	check(rules[0].Type == "formula" && strings.ReplaceAll(rules[0].Criteria, "=", "") == "$D5>0", "highlight rule is exactly deviation > 0", &results)

	chartData, chartCount := chartXML(workbook)
	check(chartCount == 1, "one category chart is present", &results)
	check(strings.Count(chartData, "<c:ser>")+strings.Count(chartData, "<ser>") == 2, "chart contains plan and actual series", &results)
	check(strings.Count(chartData, "$A$5:$A$8") >= 2, "chart categories reference all four categories", &results)
	check(strings.Contains(chartData, "$B$5:$B$8") && strings.Contains(chartData, "$C$5:$C$8"), "chart series reference plan and actual values", &results)
	check(strings.Contains(chartData, "Сумма, KZT") && strings.Contains(chartData, "План и факт по категориям"), "chart title and KZT axis unit are present", &results)

	temp, err := os.MkdirTemp("", "m08-go-verify-")
	must(err)
	defer os.RemoveAll(temp)
	changed := filepath.Join(temp, "changed.xlsx")
	copyFile(workbook, changed)
	changedBook, err := excelize.OpenFile(changed)
	must(err)
	must(changedBook.SetCellValue("План", "B2", 150000))
	// Clear stale cached formula values so LibreOffice performs a full dependency recalculation.
	must(changedBook.UpdateLinkedValue())
	must(changedBook.SetCalcProps(&excelize.CalcPropsOptions{CalcMode: ptr("auto"), FullCalcOnLoad: ptr(true), CalcOnSave: ptr(true), ForceFullCalc: ptr(true)}))
	must(changedBook.Save())
	must(changedBook.Close())
	recalculated := officeConvert(changed, "xlsx", filepath.Join(temp, "recalculated"))
	recalc, err := excelize.OpenFile(recalculated)
	must(err)
	defer recalc.Close()
	changedPlan, changedDelta := number(recalc, "План-факт", "B5"), number(recalc, "План-факт", "D5")
	check(changedPlan == 150000 && changedDelta == 0, fmt.Sprintf("changing source plan B2 to 150000 recalculates the category to plan 150000 / delta 0 (observed %.0f / %.0f)", changedPlan, changedDelta), &results)
	check(number(recalc, "План-факт", "B9") == 230000 && number(recalc, "План-факт", "D9") == 5000, "the same edit recalculates totals to plan 230000 / delta 5000 without editing totals", &results)
	recalcChart, _ := chartXML(recalculated)
	check(strings.Contains(recalcChart, "$B$5:$B$8") && strings.Contains(recalcChart, "$C$5:$C$8"), "recalculated chart remains linked to the formula result ranges", &results)

	must(os.MkdirAll(evidence, 0o755))
	pdf := officeConvert(workbook, "pdf", evidence)
	previewBase := filepath.Join(evidence, "preview")
	command := exec.Command("pdftoppm", "-f", "1", "-singlefile", "-png", pdf, previewBase)
	output, err := command.CombinedOutput()
	if err != nil {
		panic(fmt.Errorf("preview render failed: %w: %s", err, strings.TrimSpace(string(output))))
	}
	must(os.Remove(pdf))
	info, err := os.Stat(previewBase + ".png")
	must(err)
	check(info.Size() > 10000, "visual preview rendered from the XLSX first sheet and is non-empty", &results)

	report := strings.Join(results, "\n") + "\n\nWorkbook SHA-256: " + digest(workbook) + "\n"
	must(os.WriteFile(filepath.Join(evidence, "verification.txt"), []byte(report), 0o644))
	fmt.Print(report)
}
