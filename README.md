## Installation:

1. Install [climate\_utils](https://github.com/jhollowed/climate_utils)

1. Clone the package

2. Locally install the package

```bash
cd OCO_v11MIP_analysis
pip install -e .
```

The `-e` flag to `pip install` installs the package with a symlink to the soruce code, so that later updates via git pull do not require re-installation.

3. Optionally, configure data location

`export OCO_MIP_DATASETS=/desired/data/location`

4. Download the datasets

`OCO_v11MIP_analysis download all`

This will download gridded fluxes from all models in the v11 MIP, as well as the CarbonTracker region file, and OCO-2 MIP aggregate regions. The total data volume is 2.0 GB.
