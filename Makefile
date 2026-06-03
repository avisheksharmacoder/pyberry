.PHONY: build test test-tsan clean

clean:
	@echo "=> Cleaning up build artifacts..."
	rm -rf build/
	find . -name "*.c" -type f -not -path "*/vendor/*" -delete
	find . -name "*.so" -type f -delete
	rm -rf .tsan_env

build:
	python3 setup.py build_ext --inplace

# The standard, hyper-optimized test run
test: clean build
	PYTHONPATH=src python3 -m pytest tests/

# The isolated TSan diagnostic test run
test-tsan: clean
	@echo "=> Setting up isolated TSan environment..."
	rm -rf .tsan_env
	mkdir -p .tsan_env
	cp -r src tests setup.py .tsan_env/
	@echo "=> Building PyBerry with ThreadSanitizer..."
	cd .tsan_env && PYBERRY_TSAN=1 python3 setup.py build_ext --inplace
	@echo "=> Running test suite through TSan..."
	cd .tsan_env && PYTHONPATH=src TSAN_OPTIONS="suppressions=../tsan_suppressions.txt halt_on_error=1 history_size=7" python3 -m pytest tests/
	@echo "=> Cleaning up TSan environment..."
	rm -rf .tsan_env
