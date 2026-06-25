package loader

import (
	"fmt"
	"log"
	"workload_backend/pkg/models"
)

// BuildMaster loads all data sources and merges them into MasterData.
func BuildMaster(dataDir string) (*models.MasterData, error) {
	log.Println("Building master data...")
	scores, districts, maxFinalScore, err := LoadDistrictBase(dataDir)
	if err != nil {
		return nil, fmt.Errorf("failed to load district base: %v", err)
	}

	workloadItems, quantities, err := LoadAssetQuantities(dataDir)
	if err != nil {
		return nil, fmt.Errorf("failed to load asset quantities: %v", err)
	}

	pavement, err := LoadPavement(dataDir)
	if err != nil {
		return nil, fmt.Errorf("failed to load pavement: %v", err)
	}

	// Make pointer to scores
	scoresPtr := make(map[int]*models.FactorScores)
	for k, v := range scores {
		cv := v // Copy
		scoresPtr[k] = &cv
	}

	master := &models.MasterData{
		Districts:          districts,
		WorkloadItems:      workloadItems,
		Quantities:         quantities,
		Pavement:           pavement,
		FactorScores:       scoresPtr,
		GlobalMaxFactor:    maxFinalScore,
		PavementUnitCostAC: 231.02, // Hardcoded for this translation
		PavementUnitCostPC: 489.15, // Hardcoded for this translation
	}
	
	log.Println("Master data built successfully")
	return master, nil
}
