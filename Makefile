release:
	standard-version

publish:
	python setup.py sdist upload

test:
	python setup.py nosetests
