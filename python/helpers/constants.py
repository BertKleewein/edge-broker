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

DEFAULT_TOKEN_RENEWAL_INTERVAL = 3600
DEFAULT_TOKEN_RENEWAL_MARGIN = 300

if EDGEHUB_TOPIC_RULES:
    IOTHUB_API_VERSION = "2018-06-30"
else:
    IOTHUB_API_VERSION = "2019-10-01"

PROVISIONING_API_VERSION = "2019-03-31"
DIGITAL_TWIN_API_VERSION = "2020-09-30"
