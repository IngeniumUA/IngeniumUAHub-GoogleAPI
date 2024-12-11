from setuptools import setup, find_packages

setup(
    name="IngeniumUAHub-GoogleAPI",
    version="3.0",
    description="A package to integrate Google API functionalities for Calendar, Drive, Gmail, and Workspace",
    author="Yorben Joosen",
    author_email="webmaster@ingeniumua.be",
    url="https://github.com/IngeniumUA/IngeniumUAHub-GoogleAPI",
    packages=find_packages(),
    install_requires=[
        "aiogoogle"
    ],  # external packages as dependencies
)