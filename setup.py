from setuptools import setup, find_packages
setup(
    name="googleapi",
    version="38.0",
    description="A package to integrate Google API functionalities for Calendar, Drive, Gmail, and Directory",
    author="Yorben Joosen",
    author_email="webmaster@ingeniumua.be",
    url="https://github.com/IngeniumUA/IngeniumUAHub-GoogleAPI",
    packages=find_packages(),
    install_requires=[
        "aiogoogle",
        "passlib",
        "aiofiles",
        "google-auth",  # Required for google.oauth2.service_account
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "google-api-python-client"
    ],  # external packages as dependencies
)