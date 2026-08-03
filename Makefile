.PHONY: build test clean

clean:
	@echo "=> Cleaning up build artifacts..."
	rm -rf build/
	find . -name "*.c" -type f -not -path "*/vendor/*" -delete
	find . -name "*.so" -type f -delete

build:
	python3 setup.py build_ext --inplace

# The standard, hyper-optimized test run
test: clean build
	PYTHONPATH=src python3 -m pytest tests/
