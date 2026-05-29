package main

import (
	"runtime"

	"github.com/gin-gonic/gin"
)

func main() {
	// Restrict Go to use a single worker thread (1 CPU core)
	runtime.GOMAXPROCS(1)

	// Set gin to release mode for benchmarking
	gin.SetMode(gin.ReleaseMode)

	r := gin.New()

	r.GET("/", func(c *gin.Context) {
		c.String(200, "Hello from Go Gin endpoint!")
	})

	r.Run(":8000")
}
