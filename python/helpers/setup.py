# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from setuptools import setup

setup(
    name="track2",
    license="MIT License",
    author="Microsoft Corporation",
    author_email="opensource@microsoft.com",
    install_requires=["paho.mqtt>=1.5.1", "requests", "requests-unixsocket"],
)
