# GSE-FOXSI-4
GSE for calibration and flight operation of FOXSI-4.

## [Dependencies](#dependencies):
- numpy: `pip install numpy`
- PyQt6: `pip install PyQt6` (but use [PySide6 documentation](https://doc.qt.io/qtforpython/quickstart.html) from Qt, which has almost identical API to PyQt6, API differences [here](https://www.pythonguis.com/faq/pyqt6-vs-pyside6/#:~:text=PySide6%20provides%20this%20interface%20under,defining%20and%20slots%20and%20signals))
- PyQt6 Charts: `pip install PyQt6-Charts`
- pyqtgraph: `pip install pyqtgraph` ([documentation](https://www.pyqtgraph.org/))

## Setup for development:
1. `% git clone https://github.com/foxsi/GSE-FOXSI-4.git`
2. `% cd GSE-FOXSI-4`
3. Setup a virtual environment for Python:
    1. `% python -m <virtual-environment-path>` (I like to put it just in a subfolder of the git project)
    2. `% source <virtual-environment-path>/bin/activate` (see [here](https://docs.python.org/3/library/venv.html) for equivalent Windows command). This should turn your command prompt into `(<virtual-environment-path>)` followed by your usual prompt.
4. `(venv) % pip install <package>` for all the [dependencies](#dependencies). The packages should be stored locally in your virtual environment.
5. Inside `FoGSE/`, run `pip install -e .` to install the FoGSE package in an editable way. This makes it accessible to the `tests/` folder (see [here](https://stackoverflow.com/questions/6323860/sibling-package-imports/50193944#50193944) for more info on sharing Python modules to sibling directories).
6. Then, in a sibling or child folder of `FoGSE/` you should be able to `import FoGSE.<module_name>`

## Live Demos

For demos of live data, see the `demos` and `demos.live_demos` module.