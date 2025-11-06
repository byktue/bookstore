import os
import ast
from typing import List, Dict


def get_python_functions(file_path: str) -> List[str]:
    """解析Python文件，获取所有函数名（包括类方法）"""
    functions = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=file_path)

        for node in ast.walk(tree):
            # 处理普通函数
            if isinstance(node, ast.FunctionDef):
                # 保留所有函数（包括__init__等特殊方法，方便完整查看）
                functions.append(node.name)
            # 处理类中的方法
            elif isinstance(node, ast.ClassDef):
                for class_node in ast.walk(node):
                    if isinstance(class_node, ast.FunctionDef):
                        functions.append(f"{node.name}.{class_node.name}")  # 类.方法格式
    except Exception as e:
        print(f"⚠️ 跳过有问题的文件 {file_path}: {str(e)}")
        return []  # 出错时返回空列表，不影响其他文件

    return sorted(functions)


def build_directory_structure(root_dir: str) -> Dict:
    """构建目录结构，包含所有Python文件及其函数"""
    structure = {
        'name': os.path.basename(root_dir),
        'type': 'directory',
        'children': []
    }

    # 获取目录下的所有条目，并按目录优先、名称排序
    try:
        entries = sorted(os.listdir(root_dir), key=lambda x: (not os.path.isdir(os.path.join(root_dir, x)), x))
    except PermissionError:
        print(f"❌ 没有权限访问目录 {root_dir}，已跳过")
        return structure

    for entry in entries:
        entry_path = os.path.join(root_dir, entry)

        # 跳过隐藏文件/目录和__pycache__
        if entry.startswith('.') or entry == '__pycache__':
            continue

        if os.path.isdir(entry_path):
            # 递归处理子目录
            subdir_struct = build_directory_structure(entry_path)
            if subdir_struct['children'] or subdir_struct['type'] == 'file':
                structure['children'].append(subdir_struct)
        elif os.path.isfile(entry_path) and entry.endswith('.py'):
            # 处理Python文件
            functions = get_python_functions(entry_path)
            file_struct = {
                'name': entry,
                'type': 'file',
                'functions': functions
            }
            structure['children'].append(file_struct)

    return structure


def print_structure(structure: Dict, indent: int = 0, is_last: bool = True) -> None:
    """打印目录结构，按层级展示，包含函数"""
    # 处理根目录
    if indent == 0:
        print(structure['name'])
        indent += 1
    else:
        # 计算前缀
        prefix = '    ' * (indent - 1)
        if is_last:
            prefix += '└── '
        else:
            prefix += '├── '
        print(f"{prefix}{structure['name']}")

    # 打印文件的函数
    if structure['type'] == 'file' and structure['functions']:
        for i, func in enumerate(structure['functions']):
            func_is_last = i == len(structure['functions']) - 1
            func_prefix = '    ' * indent
            if func_is_last:
                func_prefix += '└── '
            else:
                func_prefix += '├── '
            print(f"{func_prefix}{func}")

    # 递归处理子节点
    if structure['type'] == 'directory' and structure['children']:
        for i, child in enumerate(structure['children']):
            child_is_last = i == len(structure['children']) - 1
            print_structure(child, indent + 1, child_is_last)


def main():
    import sys
    # 获取当前目录或命令行指定的目录
    root_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

    if not os.path.isdir(root_dir):
        print(f"错误: {root_dir} 不是有效的目录")
        return

    print(f"项目结构及函数列表 (根目录: {root_dir}):\n")
    structure = build_directory_structure(root_dir)
    print_structure(structure)


if __name__ == "__main__":
    main()