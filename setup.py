from setuptools import setup, find_packages

setup(
    name="piylang",
    version="0.1.2",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "piy=piylang.main:main"
        ]
    },
    author="Bos PiyXoX",
    description="Bahasa Pemrograman PiyLang (Indonesia Style)",
    python_requires=">=3.8",
)
