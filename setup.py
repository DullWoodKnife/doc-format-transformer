from setuptools import setup, find_packages

setup(
    name="docx2md",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "markitdown",
        "markdown",
        "weasyprint",
        "python-docx",
        "ebooklib",
        "click",
    ],
    entry_points={
        "console_scripts": [
            "docx2md=docx2md.cli:main",
        ],
    },
)
