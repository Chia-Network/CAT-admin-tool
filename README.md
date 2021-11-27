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
```

You're probably also going to want chia dev tools to make things a little easier when interacting with the node.

```
pip install chia-dev-tools --no-deps # No dependencies because we don't want to override our current chia installation
pip install pytest # This is the one dependency we need
```

Lastly this requires a synced, running wallet and the spends it outputs require a synced full node to push to
