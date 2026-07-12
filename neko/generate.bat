@echo off

openapi-python-client generate --url http://api.sc-workshop.com/docs/json --output-path %~dp0\generated --overwrite

cd %~dp0\generated

poetry build -f wheel