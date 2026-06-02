// To start the server:
// go run main.go
package main

import (
	"runtime"

	"github.com/gin-gonic/gin"
)

type TestModel struct {
	ID       int    `json:"id"`
	Name     string `json:"name"`
	IsActive bool   `json:"is_active"`
}

func main() {
	// Restrict Go to use a single worker thread (1 CPU core)
	runtime.GOMAXPROCS(1)

	// Set gin to release mode for benchmarking
	gin.SetMode(gin.ReleaseMode)

	r := gin.New()

	r.GET("/", func(c *gin.Context) {
		c.String(200, "Hello from Go Gin endpoint!")
	})

	r.POST("/test-benchmark", func(c *gin.Context) {
		var data TestModel
		if err := c.ShouldBindJSON(&data); err == nil {
			c.JSON(200, gin.H{
				"status":                 "success",
				"received_id":            data.ID,
				"received_name":          data.Name,
				"received_active_status": data.IsActive,
			})
		} else {
			c.JSON(400, gin.H{"error": err.Error()})
		}
	})

	err := r.Run(":8000")
	if err != nil {
		panic(err)
	}
}
