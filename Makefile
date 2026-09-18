# geodata.ch — Portolan catalog build
#
# `make generate` and `make validate` run anywhere (offline). The `harvest`,
# `build`, and `publish` targets need the Swiss Federal network and the proxy:
#   export HTTPS_PROXY=http://prp01.adb.intra.admin.ch:8080
#   export HTTP_PROXY=$HTTPS_PROXY

PY ?= python3

.PHONY: help generate check validate harvest build publish clean

help:
	@echo "generate  regenerate the STAC tree + README/AGENTS from tools/manifest/"
	@echo "check     fail if the generated tree is out of date"
	@echo "validate  offline structural + Portolan checks"
	@echo "harvest   verify source STAC ids and read real extents (needs proxy)"
	@echo "build     full pipeline: harvest -> convert -> enrich -> validate (needs proxy + GDAL)"
	@echo "publish   aws s3 sync catalog + assets to s3://ch-geodata (needs creds)"

generate:
	$(PY) tools/generate_catalog.py

check:
	$(PY) tools/generate_catalog.py --check

validate:
	$(PY) tools/validate.py

harvest:
	$(PY) tools/harvest_stac.py

build:
	$(PY) tools/build.py

publish:
	$(PY) tools/build.py --stages publish

clean:
	rm -rf tools/cache
