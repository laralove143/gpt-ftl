from setuptools import setup, find_packages

setup(
    name="gpt_ftl",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "colorama",
        "fluent",
        "openai",
        "tomli",
        "tomli-w",
    ],
    package_data={"gpt_ftl": ["config.toml"]},
    entry_points={
        "console_scripts": [
            "gpt-ftl=gpt_ftl.main:main",
        ],
    },
    author="Lara Kayaalp",
    author_email="me@lara.lv",
    description="Generate Fluent Translation List files using OpenAI's GPT",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/laralove143/gpt_ftl",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Localization",
    ],
    license="MIT",
    keywords="ai,fluent,ftl,gpt,llm",
)
