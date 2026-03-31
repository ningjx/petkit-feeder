#!/usr/bin/env python3
"""代码质量检查脚本."""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """运行命令并返回结果."""
    print(f"\n{'='*60}")
    print(f"检查：{description}")
    print(f"命令：{' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ {description} - 通过")
        return True
    else:
        print(f"❌ {description} - 失败")
        print(result.stdout)
        print(result.stderr)
        return False


def main():
    """主函数."""
    project_root = Path(__file__).parent
    custom_components = project_root / "custom_components" / "petkit_feeder"
    
    checks = [
        # Python 语法检查
        (
            ["python3", "-m", "py_compile"] + 
            list(custom_components.glob("**/*.py")),
            "Python 语法检查"
        ),
        
        # 导入检查
        (
            ["python3", "-c", 
             "import sys; sys.path.insert(0, '.'); "
             "from custom_components.petkit_feeder import *; "
             "print('导入成功')"],
            "模块导入检查"
        ),
    ]
    
    results = []
    for cmd, desc in checks:
        results.append(run_command(cmd, desc))
    
    print(f"\n{'='*60}")
    print(f"检查总结")
    print(f"{'='*60}")
    print(f"通过：{sum(results)}/{len(results)}")
    
    if all(results):
        print("✅ 所有检查通过！")
        return 0
    else:
        print("❌ 部分检查失败，请修复错误")
        return 1


if __name__ == "__main__":
    sys.exit(main())
