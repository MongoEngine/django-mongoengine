release:
	standard-version

release-beta:
	standard-version -p beta

publish:
	rm -rf dist
	python setup.py sdist
	twine check dist/*
	twine upload dist/*
	git push --follow-tags

test:
	poetry run python -m pytest

codegen:
	python codegen.py
	ruff format django_mongoengine/fields/__init__.py
	ruff django_mongoengine/ --fix  # It doesn't work with filename.
