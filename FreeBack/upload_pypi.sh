'''#!/bin/bash
#mypython=!python

# Upload project to pypi

rm -rf ./build
rm -rf ./dist
rm -rf ./FreeBack.egg-info

mypython setup.py sdist bdist_whell

mypython -m twine upload dist/*
'''