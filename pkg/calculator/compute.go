package calculator

import (
	"fmt"
	"math"
	"workload_backend/pkg/models"
)

// calculateDistrict handles calculation for a single district.
func calculateDistrict(master *models.MasterData, dept3 int, req models.CalculateRequest, isRevised bool) *models.CalculationResult {
	fs, ok := master.FactorScores[dept3]
	if !ok {
		return &models.CalculationResult{Dept3: dept3}
	}

	maxFactorUplift := master.GlobalMaxFactor
	useDamage := false
	if isRevised {
		maxFactorUplift = req.MaxFactorUplift
		useDamage = req.UseDamageProbability
	}

	costScalingIndex := (maxFactorUplift * fs.FinalScore) + 1.0

	quantities, ok := master.Quantities[dept3]
	if !ok {
		quantities = models.WorkloadQuantities{Quantities: make(map[string]float64)}
	}

	configSource := master.WorkloadItems
	if isRevised && len(req.CustomConfig) > 0 {
		configSource = req.CustomConfig
	}

	mergedConfig := make(map[string]models.WorkloadItem)
	for _, item := range configSource {
		cItem := item
		if isRevised {
			if over, exists := req.WorkloadOverrides[item.QuantityCol]; exists {
				if dp, ok := over["damage_probability"].(float64); ok {
					cItem.DamageProbability = dp
				}
				if uc, ok := over["unit_cost"].(float64); ok {
					cItem.UnitCost = uc
				}
				if ap, ok := over["apply_damage_probability"].(bool); ok {
					cItem.ApplyDamageProbability = ap
				}
			}
		}
		mergedConfig[item.WorkloadItem] = cItem
	}

	res := &models.CalculationResult{
		Dept3:            dept3,
		CostScalingIndex: costScalingIndex,
		Details:          make([]models.DetailResult, 0),
		DefaultQuantities: make(map[string]float64),
	}

	for _, item := range mergedConfig {
		if item.Category == "Pavement" {
			continue
		}

		qty := quantities.Quantities[item.QuantityCol]
		res.DefaultQuantities[item.QuantityCol] = qty // track baseline qty
		
		if isRevised {
			if upd, exists := req.QuantityUpdates[item.QuantityCol]; exists {
				qty = upd
			}
		}

		baseCost := qty * item.UnitCost
		if useDamage && item.ApplyDamageProbability {
			baseCost = baseCost * item.DamageProbability
		}

		factorCost := baseCost * costScalingIndex
		finalCost := factorCost

		res.BaseWorkloadCostTotal += baseCost
		res.ConditionFactorCostTotal += (factorCost - baseCost)
		res.FinalCostTotal += finalCost

		res.Details = append(res.Details, models.DetailResult{
			WorkloadItem:        item.WorkloadItem,
			Quantity:            qty,
			Unit:                item.Unit,
			Category:            item.Category,
			DamageProbability:   item.DamageProbability,
			UnitCost:            item.UnitCost,
			BaseWorkloadCost:    baseCost,
			ConditionFactorCost: (factorCost - baseCost),
			FinalCost:           finalCost,
		})
	}

	paveBaseTotal := 0.0
	paveFactorTotal := 0.0

	if p, ok := master.Pavement[dept3]; ok {
		acCost := p.ACArea * master.PavementUnitCostAC
		acFactorCost := acCost * costScalingIndex
		paveBaseTotal += acCost
		paveFactorTotal += (acFactorCost - acCost)
		res.Details = append(res.Details, models.DetailResult{
			WorkloadItem:        "ผิวทาง AC",
			Quantity:            p.ACArea,
			Unit:                "ตร.ม.",
			Category:            "Pavement",
			DamageProbability:   1.0,
			UnitCost:            master.PavementUnitCostAC,
			BaseWorkloadCost:    acCost,
			ConditionFactorCost: (acFactorCost - acCost),
			FinalCost:           acFactorCost,
		})

		pcCost := p.PCArea * master.PavementUnitCostPC
		pcFactorCost := pcCost * costScalingIndex
		paveBaseTotal += pcCost
		paveFactorTotal += (pcFactorCost - pcCost)
		res.Details = append(res.Details, models.DetailResult{
			WorkloadItem:        "ผิวทาง PC",
			Quantity:            p.PCArea,
			Unit:                "ตร.ม.",
			Category:            "Pavement",
			DamageProbability:   1.0,
			UnitCost:            master.PavementUnitCostPC,
			BaseWorkloadCost:    pcCost,
			ConditionFactorCost: (pcFactorCost - pcCost),
			FinalCost:           pcFactorCost,
		})

		otherCost := p.OtherArea * master.PavementUnitCostAC
		otherFactorCost := otherCost * costScalingIndex
		paveBaseTotal += otherCost
		paveFactorTotal += (otherFactorCost - otherCost)
	}

	res.PavementBaseCostTotal = paveBaseTotal
	res.PavementFactorCostTotal = paveFactorTotal
	res.PavementFinalCostTotal = paveBaseTotal + paveFactorTotal

	res.TotalGrandFinalCost = res.FinalCostTotal + res.PavementFinalCostTotal
	res.TotalGrandFinalCost = math.Round(res.TotalGrandFinalCost*100) / 100

	return res
}

// Calculate processes the workload cost based on input overrides and computes metrics.
func Calculate(master *models.MasterData, req models.CalculateRequest) (*models.CalculationResult, error) {
	if master == nil {
		return nil, fmt.Errorf("master data is nil")
	}

	dept3 := req.SelectedDept3
	if dept3 == 0 && len(master.Districts) > 0 {
		dept3 = master.Districts[0].Dept3
	}

	// Calculate for selected district (revised)
	res := calculateDistrict(master, dept3, req, true)
	
	// Calculate for selected district (baseline) to get baseline total
	baseRes := calculateDistrict(master, dept3, req, false)

	// Build Breakdown
	res.Breakdown = []models.BreakdownItem{
		{Component: "Workload Base Cost", Baseline: baseRes.BaseWorkloadCostTotal, Revised: res.BaseWorkloadCostTotal},
		{Component: "Condition Factor Cost", Baseline: baseRes.ConditionFactorCostTotal, Revised: res.ConditionFactorCostTotal},
		{Component: "Pavement Base Cost", Baseline: baseRes.PavementBaseCostTotal, Revised: res.PavementBaseCostTotal},
		{Component: "Pavement Factor Cost", Baseline: baseRes.PavementFactorCostTotal, Revised: res.PavementFactorCostTotal},
		{Component: "Total Final Cost", Baseline: baseRes.TotalGrandFinalCost, Revised: res.TotalGrandFinalCost},
	}

	// Initialize national metrics and chart data
	res.Metrics = models.Metrics{
		BaselineTotal: baseRes.TotalGrandFinalCost,
		RevisedTotal:  res.TotalGrandFinalCost,
	}
	res.ChartData = models.ChartData{
		AllDistrictsBaseline: make([]models.ChartDataItem, 0),
		AllDistrictsRevised:  make([]models.ChartDataItem, 0),
	}

	// Loop over all districts for national metrics
	for _, d := range master.Districts {
		dBase := calculateDistrict(master, d.Dept3, req, false)
		dRev := calculateDistrict(master, d.Dept3, req, true)

		res.Metrics.NationalBaseline += dBase.TotalGrandFinalCost
		res.Metrics.NationalRevised += dRev.TotalGrandFinalCost

		res.ChartData.AllDistrictsBaseline = append(res.ChartData.AllDistrictsBaseline, models.ChartDataItem{
			Dept3:            d.Dept3,
			DistrictName:     d.DistrictName,
			TotalBudgetModel: dBase.TotalGrandFinalCost,
		})
		res.ChartData.AllDistrictsRevised = append(res.ChartData.AllDistrictsRevised, models.ChartDataItem{
			Dept3:            d.Dept3,
			DistrictName:     d.DistrictName,
			TotalBudgetModel: dRev.TotalGrandFinalCost,
		})
	}

	return res, nil
}
