## Installation:

1. Clone the package

2. Locally install the package

    cd OCO_v11MIP_analysis
    pip install -e

The `-e` flag to `pip install` installs the package with a symlink to the soruce code, so that later updates via git pull do not require re-installation.

3. Optionally, configure data location

    export OCO_MIP_DATASETS=/desired/data/location 

4. Download the datasets

    OCO_v11MIP_analysis download all
