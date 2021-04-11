release:
	standard-version

release-beta:
	standard-version -p beta

publish:
	python setup.py sdist
	twine upload dist/*

test:
	poetry run python -m pytest
