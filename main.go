package main

import (
	"log"
	"net/http"

	"workload_backend/pkg/calculator"
	"workload_backend/pkg/loader"
	"workload_backend/pkg/models"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

var masterDataCache *models.MasterData

func main() {
	log.Println("Starting Workload API Server in Go...")

	// Pre-load data into memory
	var err error
	masterDataCache, err = loader.BuildMaster("data")
	if err != nil {
		log.Fatalf("Failed to build master data: %v", err)
	}

	r := gin.Default()

	// Configure CORS
	r.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"*"},
		AllowMethods:     []string{"GET", "POST", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Accept"},
		AllowCredentials: true,
	}))

	api := r.Group("/api")
	{
		api.GET("/init", handleInit)
		api.POST("/calculate", handleCalculate)
	}

	r.GET("/", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "ok", "message": "Workload API (Go) is running"})
	})

	log.Println("Server listening on port 8001")
	if err := r.Run("0.0.0.0:8001"); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}

func handleInit(c *gin.Context) {
	if masterDataCache == nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Master data not loaded"})
		return
	}

	resp := models.InitResponse{
		Districts:       masterDataCache.Districts,
		ParamGrid:       masterDataCache.WorkloadItems,
		MaxFactorUplift: 0.15,
	}
	c.JSON(http.StatusOK, resp)
}

func handleCalculate(c *gin.Context) {
	var req models.CalculateRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if masterDataCache == nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Master data not loaded"})
		return
	}

	result, err := calculator.Calculate(masterDataCache, req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, result)
}
