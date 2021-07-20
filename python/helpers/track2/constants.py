# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

# TODO: document all of these constants

# what rules should we use for building topic strings?
# True = New EdgeHub topic rules.
# False = Old IotHub topic rules.
EDGEHUB_TOPIC_RULES = False

# Defult expiration period, in seconds, of any passwords (SAS tokens) created by this code
DEFAULT_PASSWORD_RENEWAL_INTERVAL = 3600

# Number of seconds before a password (SAS token) expires that this code will create a new password.
DEFAULT_PASSWORD_RENEWAL_MARGIN = 300

# API version string for IOTHub APIs
EDGEHUB_PREVIEW_API_VERSION = "2018-06-30"
IOTHUB_V1_API_VERSION = "2019-10-01"
IOTHUB_V2_API_VERSION = "2020-06-30-preview"

# Interface ID for Azure Security Center messages
SECURITY_MESSAGE_INTERFACE_ID = "urn:azureiot:Security:SecurityAgent:1"

# string encoding to use when converting between strings and byte arrays
DEFAULT_STRING_ENCODING = "utf-8"

# default content type
DEFAULT_CONTENT_TYPE = "application/json"
