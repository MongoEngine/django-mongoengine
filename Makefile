release:
	standard-version

release-beta:
	standard-version -p beta

publish:
	rm -rf dist
	python setup.py sdist
	twine check dist/*
	twine upload dist/*

test:
	poetry run python -m pytest
