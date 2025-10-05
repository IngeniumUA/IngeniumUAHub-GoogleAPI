# IngeniumUAHub-GoogleAPI

```git+https://github.com/IngeniumUA/IngeniumUAHub-GoogleAPI.git```

# Directory API links
1. [Directory API documentation](https://developers.google.com/admin-sdk/directory/reference/rest)
2. [Hashing library](https://passlib.readthedocs.io/en/stable/lib/passlib.hash.sha256_crypt.html)
3. [Group Settings API](https://developers.google.com/admin-sdk/groups-settings/v1/reference/groups#json)

# Calendar API links
1. [Calendar API documentation](https://developers.google.com/calendar/api/v3/reference)
2. [ACL API documentation to share calendars](https://developers.google.com/calendar/api/v3/reference/acl)

# Gmail API links
1. [Gmail API documentation](https://developers.google.com/gmail/api/guides)
2. [MIME documentation](https://docs.python.org/3/library/email.mime.html)

# Drive API links
1. [Drive API documentation](https://developers.google.com/drive/api/reference/rest/v3)

# Geocoding API links
1. [Geocoding API documentation](https://developers.google.com/maps/documentation/geocoding/overview)

# Wallet API links
1. [Wallet API documentation](https://developers.google.com/wallet/generic)

# General links
1. [OAuthScopes](https://developers.google.com/identity/protocols/oauth2/scopes)
2. [Connect to service account](https://developers.google.com/analytics/devguides/config/mgmt/v3/quickstart/service-py)

# Auto creating TypedDicts
1. [GitHub link](https://github.com/koxudaxi/datamodel-code-generator)

```
pip install datamodel-code-generator
datamodel-codegen --input input_file --output output_file --input-file-type json --output-model-type typing.TypedDict
```
# Setting up service accounts
Note: The service accounts don't need roles, you just need to create them and give them the right permissions in the workspace admin panel using the second link.
1. [Creating service accounts](https://console.cloud.google.com/iam-admin/serviceaccounts?inv=1&invt=AbkM9Q&project=ingeniumuahub)
2. [Domain wide delegation acces](https://developers.google.com/identity/protocols/oauth2/service-account#delegatingauthority)