from setuptools import setup, find_packages

setup(
    name="scrcpy-gui",
    version="1.0.0",
    description="Libadwaita graphical interface for scrcpy",
    author="Scrcpy GUI Team",
    packages=find_packages(),
    py_modules=["main", "window"],
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "scrcpy-gui=main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX :: Linux",
    ],
)
