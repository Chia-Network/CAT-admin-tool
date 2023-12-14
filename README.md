CAT Admin Tool
=======

Install
-------

**Ubuntu/MacOSs**
```
git clone https://github.com/Chia-Network/CAT-admin-tool.git
cd CAT-admin-tool
python3 -m venv venv
. ./venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install .
pip install chia-dev-tools --no-deps
pip install pytest
```
(If you're on an M1 Mac, make sure you are running an ARM64 native python virtual environment)

**Windows Powershell**
```
git clone https://github.com/Chia-Network/CAT-admin-tool.git
cd CAT-admin-tool
py -m venv venv
./venv/Scripts/activate
python -m pip install --upgrade pip setuptools wheel
pip install .
pip install chia-dev-tools --no-deps
pip install pytest
```

Lastly this requires a synced, running light wallet

Verify the installation was successful
```
cats --help
cdv --help
```

Examples can be found in the [CAT Creation Tutorial](https://docs.chia.net/guides/cat-creation-tutorial/#cat-admin-tool)
