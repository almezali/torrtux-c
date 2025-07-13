from setuptools import setup

setup(
    name="torrtux",
    version="1.0.3",
    description="A Professional Multi-Source Torrent Search Tool for Command Line",
    author="Mahmoud Almezali",
    author_email="mzmcsmzm@gmail.com",
    url="https://github.com/almezali/torrtux-c",
    py_modules=['torrtux'],
    install_requires=[
        "requests",
        "beautifulsoup4",
        "tabulate",
        "termcolor",
        "tqdm"
    ],
    entry_points={
        'console_scripts': [
            'torrtux=torrtux:main'
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
    ],
    python_requires=">=3.6"
)

