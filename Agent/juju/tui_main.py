import os
import sys

# 支持直接运行 `py tui_main.py`：把 juju 包所在目录加入 sys.path
_package_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_package_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from juju.tui.app import run

if __name__ == "__main__":
    run()
