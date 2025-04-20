release:
	standard-version

release-beta:
	standard-version -p beta

publish:
	rm -rf dist
	python -m build --installer uv
	twine check dist/*
	twine upload dist/*
	git push --follow-tags

test:
	pytest

codegen:
	python codegen.py
	ruff format django_mongoengine/fields/__init__.py
	ruff django_mongoengine/ --fix  # It doesn't work with filename.
