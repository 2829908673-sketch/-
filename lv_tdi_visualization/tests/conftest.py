"""让项目目录及仓库根目录中的 pytest 命令使用同一份源码。"""

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
