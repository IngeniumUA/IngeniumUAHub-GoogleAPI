from setuptools import setup, find_packages
setup(
    name="googleapi",
    version="31.0",
    description="A package to integrate Google API functionalities for Calendar, Drive, Gmail, and Directory",
    author="Yorben Joosen",
    author_email="webmaster@ingeniumua.be",
    url="https://github.com/IngeniumUA/IngeniumUAHub-GoogleAPI",
    packages=find_packages(),
    install_requires=[
        "aiogoogle",
        "passlib",
        "aiofiles"
    ],  # external packages as dependencies
)