from setuptools import setup, find_packages

setup(
    name="HSparkAPI",
    version="0.1",
    description="Python wrapper for the (unofficial) HARMAN Spark API",
    long_description="Python wrapper for the (unofficial) HARMAN Spark API used by the HARMAN Spark web portal.",
    author="abchev",
    author_email="alex@abchev.com",
    license="MIT",
    url="https://github.com/abchev/HSparkAPI",
    packages=find_packages(),
    python_requires=">=3.6",
    install_requires=[
        "requests==2.28.1",
        "selenium==4.9.1",
        "webdriver-manager==3.8.6",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
    ],
)