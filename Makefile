release:
	standard-version

release-beta:
	standard-version -p beta

publish:
	python setup.py sdist upload

test:
	poetry run python -m pytest
