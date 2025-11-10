from setuptools import setup, find_packages

setup(
    name="project_warp",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.119.1",
        "uvicorn>=0.23,<0.30",
        "httpx==0.27.0",
        "pydantic>=2.5,<2.10",
        "pydantic-settings==2.2.1",
        "python-dotenv==1.0.1",
    ],
)