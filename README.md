# Quick CLI for exploring the FB graphql api

Literally tossed together in a few hours to save time inspecting what fields are actually supported since the FB api docs I find super frustrating to read through and understand.

example usage:
```bash
    example: python main.py call-gql --url='{campaign_id}/insights' \
      --fields="..." --filter='["data"]' fields can be a gigantic comma separated string listing of all the fields that could possibly exist
      --filter just simplifies the output acceptable fstrings in url are: {'campaign_id', 'account_id', 'adset_id', 'ad_id'} which will use the specific subcommand to pull the first id for that object type and perform a replacement.

    output:
    {
        "unsupported_fields": [/* fields which gave back an error */],
        "unfound_fields": [/* fields weren't returned, no error caused */],
        "found_fields": [/* fields you should see in result*/]
        "result": {/* the fields and values found in the response */}
    }
```