package models

// District represents basic information about a district.
type District struct {
	Dept3         int     `json:"dept3"`
	DivisionName  string  `json:"division_name"`
	DistrictName  string  `json:"district_name"`
	DistrictLabel string  `json:"district_label"`
}

// FactorScores represents the raw and normalized scores for a district.
type FactorScores struct {
	Dept3               int
	TrafficScoreRaw     float64
	TruckScoreRaw       float64
	ElevationScoreRaw   float64
	RainScoreRaw        float64
	OperatingDistanceRaw float64

	TrafficScorePct     float64
	TruckScorePct       float64
	ElevationScorePct   float64
	RainScorePct        float64
	OpDistScorePct      float64

	FinalScore          float64
	CostScalingIndex    float64
}

// WorkloadItem represents a single row of configuration from the grid.
type WorkloadItem struct {
	WorkloadItem           string  `json:"workload_item"`
	QuantityCol            string  `json:"quantity_col"`
	Unit                   string  `json:"unit"`
	DamageProbability      float64 `json:"damage_probability"`
	ApplyDamageProbability bool    `json:"apply_damage_probability"`
	UnitCost               float64 `json:"unit_cost"`
	Category               string  `json:"category"`
	PriorityScore          float64 `json:"priority_score"`
}

// PavementQuantities holds the pavement data.
type PavementQuantities struct {
	Dept3     int
	ACArea    float64 // "ผิวทาง AC (ตร.ม.)"
	PCArea    float64 // "ผิวทาง PC (ตร.ม.)"
	OtherArea float64 // "ผิวทางอื่นๆ (ตร.ม.)"
	ParaArea  float64 // "ผิวทาง PARA (ตร.ม.)"
}

// WorkloadQuantities holds the asset quantities read from the Excel file.
type WorkloadQuantities struct {
	Dept3      int
	Quantities map[string]float64
}

// MasterData holds all the loaded data.
type MasterData struct {
	Districts          []District
	WorkloadItems      []WorkloadItem
	Quantities         map[int]WorkloadQuantities
	Pavement           map[int]PavementQuantities
	FactorScores       map[int]*FactorScores
	PavementUnitCostAC float64
	PavementUnitCostPC float64
	GlobalMaxFactor    float64
}

// CalculateRequest is the payload from the frontend.
type CalculateRequest struct {
	SelectedDept3        int                               `json:"selected_dept3"`
	MaxFactorUplift      float64                           `json:"max_factor_uplift"`
	UseDamageProbability bool                              `json:"use_damage_probability"`
	WorkloadOverrides    map[string]map[string]interface{} `json:"workload_overrides"`
	QuantityUpdates      map[string]float64                `json:"quantity_updates"`
	CustomConfig         []WorkloadItem                    `json:"custom_config"`
}

// InitResponse is the payload for /api/init.
type InitResponse struct {
	Districts       []District     `json:"districts"`
	ParamGrid       []WorkloadItem `json:"param_grid"`
	MaxFactorUplift float64        `json:"max_factor_uplift"`
}

// DetailResult represents the detailed calculation for a single workload item.
type DetailResult struct {
	WorkloadItem         string  `json:"workload_item"`
	Quantity             float64 `json:"quantity"`
	Unit                 string  `json:"unit"`
	Category             string  `json:"category"`
	DamageProbability    float64 `json:"damage_probability"`
	UnitCost             float64 `json:"unit_cost"`
	BaseWorkloadCost     float64 `json:"base_workload_cost"`
	ConditionFactorCost  float64 `json:"condition_factor_cost"`
	FinalCost            float64 `json:"final_cost"`
}

type Metrics struct {
	BaselineTotal    float64 `json:"baseline_total"`
	RevisedTotal     float64 `json:"revised_total"`
	NationalBaseline float64 `json:"national_baseline"`
	NationalRevised  float64 `json:"national_revised"`
}

type ChartDataItem struct {
	Dept3            int     `json:"dept3"`
	DistrictName     string  `json:"district_name"`
	TotalBudgetModel float64 `json:"total_budget_model"`
}

type ChartData struct {
	AllDistrictsBaseline []ChartDataItem `json:"all_districts_baseline"`
	AllDistrictsRevised  []ChartDataItem `json:"all_districts_revised"`
}

type BreakdownItem struct {
	Component string  `json:"component"`
	Baseline  float64 `json:"baseline"`
	Revised   float64 `json:"revised"`
}

// CalculationResult is the response payload for /api/calculate.
type CalculationResult struct {
	Dept3                     int                `json:"dept3"`
	BaseWorkloadCostTotal     float64            `json:"base_workload_cost_total"`
	ConditionFactorCostTotal  float64            `json:"condition_factor_cost_total"`
	FinalCostTotal            float64            `json:"final_cost_total"`
	PavementBaseCostTotal     float64            `json:"pavement_base_cost_total"`
	PavementFactorCostTotal   float64            `json:"pavement_factor_cost_total"`
	PavementFinalCostTotal    float64            `json:"pavement_final_cost_total"`
	TotalGrandFinalCost       float64            `json:"total_grand_final_cost"`
	CostScalingIndex          float64            `json:"cost_scaling_index"`
	Details                   []DetailResult     `json:"details"`
	Metrics                   Metrics            `json:"metrics"`
	ChartData                 ChartData          `json:"chart_data"`
	Breakdown                 []BreakdownItem    `json:"breakdown"`
	DefaultQuantities         map[string]float64 `json:"default_quantities"`
}
