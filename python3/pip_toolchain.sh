# cd eventdispatch/python3/

rm -rf dist/
python3 -m build
twine upload dist/*

