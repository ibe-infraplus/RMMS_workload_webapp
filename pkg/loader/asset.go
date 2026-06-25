package loader

import (
	"fmt"
	"path/filepath"
	"strconv"
	"workload_backend/pkg/models"
	"github.com/xuri/excelize/v2"
)

// LoadAssetQuantities loads workload items configuration and the asset quantities per district.
func LoadAssetQuantities(dataDir string) ([]models.WorkloadItem, map[int]models.WorkloadQuantities, error) {
	filePath := filepath.Join(dataDir, "group_data_final.xlsx")
	f, err := excelize.OpenFile(filePath)
	if err != nil {
		return nil, nil, fmt.Errorf("failed to open group_data_final: %v", err)
	}
	defer f.Close()

	// 1. Read input sheet for config
	inputRows, err := f.GetRows("input")
	if err != nil {
		return nil, nil, fmt.Errorf("failed to read input sheet: %v", err)
	}
	
	if len(inputRows) < 2 {
		return nil, nil, fmt.Errorf("no data in input sheet")
	}

	headerInput := inputRows[0]
	inColIdx := make(map[string]int)
	for i, c := range headerInput {
		inColIdx[c] = i
	}

	workloadItems := make([]models.WorkloadItem, 0)
	for _, row := range inputRows[1:] {
		if len(row) == 0 {
			continue
		}
		item := getColSafe(row, inColIdx["workload_item"])
		if item == "" {
			continue
		}

		wItem := models.WorkloadItem{
			WorkloadItem:      item,
			QuantityCol:       getColSafe(row, inColIdx["quantity_col"]),
			Unit:              getColSafe(row, inColIdx["unit"]),
			DamageProbability: parseFloatSafe(getColSafe(row, inColIdx["damage_probability"])),
			UnitCost:          parseFloatSafe(getColSafe(row, inColIdx["unit_cost"])),
			Category:          getColSafe(row, inColIdx["category"]),
			PriorityScore:     parseFloatSafe(getColSafe(row, inColIdx["priority_score"])),
		}
		
		applyProb := getColSafe(row, inColIdx["apply_damage_probability"])
		if applyProb == "True" || applyProb == "true" || applyProb == "1" {
			wItem.ApplyDamageProbability = true
		} else {
			wItem.ApplyDamageProbability = false
		}

		workloadItems = append(workloadItems, wItem)
	}

	// 2. Read ASSET sheet for quantities
	assetRows, err := f.GetRows("ASSET")
	if err != nil {
		return nil, nil, fmt.Errorf("failed to read ASSET sheet: %v", err)
	}
	
	if len(assetRows) < 2 {
		return nil, nil, fmt.Errorf("no data in ASSET sheet")
	}

	headerAsset := assetRows[0]
	asColIdx := make(map[string]int)
	for i, c := range headerAsset {
		asColIdx[c] = i
	}

	quantities := make(map[int]models.WorkloadQuantities)
	for _, row := range assetRows[1:] {
		if len(row) == 0 {
			continue
		}
		dept3Str := getColSafe(row, asColIdx["dept3"])
		if dept3Str == "" {
			continue
		}
		dept3, err := strconv.Atoi(dept3Str)
		if err != nil {
			continue
		}

		q := models.WorkloadQuantities{
			Dept3:      dept3,
			Quantities: make(map[string]float64),
		}

		for _, item := range workloadItems {
			if item.QuantityCol != "" {
				valStr := getColSafe(row, asColIdx[item.QuantityCol])
				q.Quantities[item.QuantityCol] = parseFloatSafe(valStr)
			}
		}

		quantities[dept3] = q
	}

	return workloadItems, quantities, nil
}

// LoadPavement loads pavement quantities from operating_distances.xlsx
func LoadPavement(dataDir string) (map[int]models.PavementQuantities, error) {
	filePath := filepath.Join(dataDir, "operating_distances.xlsx")
	f, err := excelize.OpenFile(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open operating_distances: %v", err)
	}
	defer f.Close()

	rows, err := f.GetRows("Sheet1") // Assuming data is in Sheet1
	if err != nil || len(rows) < 2 {
		return nil, fmt.Errorf("failed to read operating_distances or no data: %v", err)
	}

	headers := rows[0]
	colIdx := make(map[string]int)
	for i, c := range headers {
		colIdx[c] = i
	}

	pavementMap := make(map[int]models.PavementQuantities)
	for _, row := range rows[1:] {
		if len(row) == 0 {
			continue
		}
		dept3Str := getColSafe(row, colIdx["dept3"])
		if dept3Str == "" {
			continue
		}
		dept3, err := strconv.Atoi(dept3Str)
		if err != nil {
			continue
		}

		p := models.PavementQuantities{
			Dept3:     dept3,
			ACArea:    parseFloatSafe(getColSafe(row, colIdx["ผิวทาง AC (ตร.ม.)"])),
			PCArea:    parseFloatSafe(getColSafe(row, colIdx["ผิวทาง PC (ตร.ม.)"])),
			OtherArea: parseFloatSafe(getColSafe(row, colIdx["ผิวทางอื่นๆ (ตร.ม.)"])),
			ParaArea:  parseFloatSafe(getColSafe(row, colIdx["ผิวทาง PARA (ตร.ม.)"])),
		}
		pavementMap[dept3] = p
	}

	return pavementMap, nil
}
