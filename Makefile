.PHONY: install-core install-full test fetch-synth run-synth

install-core:
	python -m pip install -U pip
	pip install -e ".[core]"

install-full:
	python -m pip install -U pip
	pip install -e ".[full]"

test:
	pytest

fetch-synth:
	compass fetch synthetic_v1

run-synth:
	compass run configs/recipes/synthetic.yaml
