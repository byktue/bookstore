import setuptools

# 读取项目描述文件（通常README README.md 内容将作为长描述）
with open("README.md", "r") as fh:
    long_description = fh.read()

# 配置 Python 包的元数据和安装信息
setuptools.setup(
    name="bookstore",  # 包名称（PyPI 上的唯一标识）
    version="0.0.1",   # 版本号（遵循语义化版本规范）
    author="DaSE-DBMS",  # 作者名称
    author_email="DaSE-DBMS@DaSE-DBMS.com",  # 作者邮箱
    description="Buy Books Online",  # 包的简短描述
    long_description=long_description,  # 长描述（来自 README.md）
    long_description_content_type="text/markdown",  # 长描述的格式
    url="https://github.com/DaSE-DBMS/bookstore.git",  # 项目主页（通常是 GitHub 仓库）
    packages=setuptools.find_packages(),  # 自动发现并包含所有 Python 包
    classifiers=[
        # 包的分类信息（用于 PyPI 索引和筛选）
        "Programming Language :: Python :: 3",  # 支持的 Python 版本
        "License :: OSI Approved :: MIT License",  # 开源许可证
        "Operating System :: OS Independent",  # 支持的操作系统（跨平台）
    ],
    python_requires=">=3.6",  # 最低支持的 Python 版本
)