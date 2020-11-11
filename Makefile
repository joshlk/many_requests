# Add to PHONY target list so it always it run even when nothing has changed
.PHONY: dist install clean venv-create venv-activate docs check-dist test-pypi pypi-upload

dist:
	python setup.py sdist bdist_wheel

install:
	pip install .

clean:
	$(RM) -r build dist src/*.egg-info
	$(RM) -r .pytest_cache
	find . -name __pycache__ -exec rm -r {} +
	#git clean -fdX

venv-create:
	python -m venv dataclassframe-venv
	source dataclassframe-venv/bin/activate

venv-activate:
	# Doesn't work. Need to execute manually
	source dataclassframe-venv/bin/activate

venv-delete:
	rm -rf dataclassframe-venv

docs:
	sphinx-build -a -E -b html docs_source docs

check-dist:
	twine check dist/*

test-pypi:
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

pypi-upload:
	twine upload dist/*