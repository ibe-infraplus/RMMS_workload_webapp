package calculator

import (
	"fmt"
	"math"
	"workload_backend/pkg/models"
)

// Calculate processes the workload cost based on input overrides.
func Calculate(master *models.MasterData, req models.CalculateRequest) (*models.CalculationResult, error) {
	if master == nil {
		return nil, fmt.Errorf("master data is nil")
	}
	
	// Default to first district if 0
	dept3 := req.SelectedDept3
	if dept3 == 0 && len(master.Districts) > 0 {
		dept3 = master.Districts[0].Dept3
	}

	// 1. Get Factor Score for Dept3
	fs, ok := master.FactorScores[dept3]
	if !ok {
		return nil, fmt.Errorf("factor score not found for district %d", dept3)
	}

	// Calculate Cost Scaling Index
	// Index = (max_uplift * score) + 1.0
	// To match Python logic: score is normalized (0 to 1)
	costScalingIndex := (req.MaxFactorUplift * fs.FinalScore) + 1.0

	quantities, ok := master.Quantities[dept3]
	if !ok {
		quantities = models.WorkloadQuantities{Quantities: make(map[string]float64)}
	}

	// Merge config with overrides
	mergedConfig := make(map[string]models.WorkloadItem)
	configSource := master.WorkloadItems
	if len(req.CustomConfig) > 0 {
		configSource = req.CustomConfig
	}

	for _, item := range configSource {
		cItem := item
		
		// Apply workload overrides (DamageProb and UnitCost)
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
		mergedConfig[item.WorkloadItem] = cItem
	}

	res := &models.CalculationResult{
		Dept3:            dept3,
		CostScalingIndex: costScalingIndex,
		Details:          make([]models.DetailResult, 0),
	}

	// 2. Asset & Policy Workloads
	for _, item := range mergedConfig {
		// Pavement is handled separately below, although we can skip it here if category is Pavement
		if item.Category == "Pavement" {
			continue
		}

		qty := quantities.Quantities[item.QuantityCol]
		// Apply quantity overrides
		if upd, exists := req.QuantityUpdates[item.QuantityCol]; exists {
			qty = upd
		}

		baseCost := qty * item.UnitCost
		if req.UseDamageProbability && item.ApplyDamageProbability {
			baseCost = baseCost * item.DamageProbability
		}

		factorCost := baseCost * costScalingIndex
		finalCost := factorCost

		res.BaseWorkloadCostTotal += baseCost
		res.ConditionFactorCostTotal += (factorCost - baseCost) // Just the delta
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

	// 3. Pavement Workload
	paveBaseTotal := 0.0
	paveFactorTotal := 0.0

	if p, ok := master.Pavement[dept3]; ok {
		// Skin AC
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

		// Skin PC
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

		// Other Pavement logic follows similar structure (simplified here for brevity)
		// For now we add a generic Other/Para
		otherCost := p.OtherArea * master.PavementUnitCostAC // Using AC cost as fallback
		otherFactorCost := otherCost * costScalingIndex
		paveBaseTotal += otherCost
		paveFactorTotal += (otherFactorCost - otherCost)
	}

	res.PavementBaseCostTotal = paveBaseTotal
	res.PavementFactorCostTotal = paveFactorTotal
	res.PavementFinalCostTotal = paveBaseTotal + paveFactorTotal

	res.TotalGrandFinalCost = res.FinalCostTotal + res.PavementFinalCostTotal

	// Rounding helper (optional)
	res.TotalGrandFinalCost = math.Round(res.TotalGrandFinalCost*100) / 100

	return res, nil
}
