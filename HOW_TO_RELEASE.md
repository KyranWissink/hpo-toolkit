# How to release

The document describes how to release `hpo-toolkit` to *PyPi* and `conda-forge`.

##### Release checklist

- update documentation notebooks
- create a release branch
- bump versions to a release:
  - `src/hpotk/__init__.py`
  - `recipe/meta.yaml`
- ensure the CI passes, check that coverage levels are acceptable
- deploy to PyPi (described below)
- merge to `master`
- merge `master` to `development`
- bump versions to a dev version


##### Uploading to conda-forge
```bash
# https://conda-forge.org/#contribute
```

#### PyPi

The following packages are required for testing, building, and deployment to PyPi:
- `tox`
- `build`
- `twine`

Consider creating a dedicated virtual environment with the above packages. Then, run the following 
to deploy `hpo-toolkit` to PyPi:  

```bash
cd hpo-toolkit

# Test
tox run

# Build
python -m build

# Deploy
python -m twine upload --sign --identity <YOUR_GPG_KEY_HERE> dist/*
```

The commands will run tests, build source distribution and a wheel, and deploy the source distribution and wheel to PyPi.
During deployment, you will be prompted for your PyPi credentials.  
