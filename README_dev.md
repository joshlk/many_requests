
# Build and push to PyPi
Requires: `pip install twine`
Don't forget to increment version number

Bump version (major, minor or micro):

```shell script
bump2version micro
```

Build dist

```shell script
make dist
```

Upload to test PyPi

```shell script
make check-dist
make test-pypi
```

Activate virtual env (might need to `make venv-create`)

```shell script
source many_requests-venv/bin/activate
```

Test install (in virtual env):

```shell script
pip install --upgrade --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple many_requests
```

Then push to real PyPI:

```shell script
rm -r dist
make dist
make pypi-upload
```
