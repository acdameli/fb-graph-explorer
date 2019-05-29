# Quick CLI for exploring the FB graphql api

Literally tossed together in a few hours to save time inspecting what fields are actually supported since the FB api docs I find super frustrating to read through and understand.

usage:
```
    usage: python main.py call-gql --url='{campaign_id}/insights' \
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
example:
```
 $ python main.py call-gql --url='{campaign_id}/insights' --fields=account_currency,account_id,account_name,action_values,actions,ad_id,ad_name,adset_id,adset_name,app_store_clicks,buying_type,campaign_id,campaign_name,canvas_avg_view_percent,canvas_avg_view_time,clicks,cost_per_10_sec_video_view,cost_per_action_type,cost_per_estimated_ad_recallers,cost_per_inline_link_click,cost_per_inline_post_engagement,cost_per_outbound_click,cost_per_thruplay,cost_per_unique_action_type,cost_per_unique_click,cost_per_unique_inline_link_click,cost_per_unique_outbound_click,cpc,cpm,cpp,ctr,date_start,date_stop,deeplink_clicks,estimated_ad_recall_rate,estimated_ad_recallers,frequency,impressions,inline_link_click_ctr,inline_link_clicks,inline_post_engagement,mobile_app_purchase_roas,newsfeed_avg_position,newsfeed_clicks,newsfeed_impressions,objective,outbound_clicks,outbound_clicks_ctr,purchase_roas,reach,relevance_score,social_spend,spend,unique_actions,unique_clicks,unique_ctr,unique_impressions,unique_inline_link_click_ctr,unique_inline_link_clicks,unique_link_clicks_ctr,unique_outbound_clicks,unique_outbound_clicks_ctr,video_10_sec_watched_actions,video_30_sec_watched_actions,video_avg_percent_watched_actions,video_avg_time_watched_actions,video_complete_watched_actions,video_p100_watched_actions,video_p25_watched_actions,video_p50_watched_actions,video_p75_watched_actions,video_p95_watched_actions,video_play_actions,video_thruplay_watched_actions,website_clicks,website_ctr,website_purchase_roas --filter='["data"]'
     
reattempting request with supported_fields
{
    "object_ids": {
        "account_id": __REDACTED__
    },
    "result": {
        "account_currency": "USD",
        "account_id": __REDACTED__,
        "account_name": __REDACTED__,
        "buying_type": "AUCTION",
        "campaign_id": __REDACTED__,
        "campaign_name": __REDACTED__,
        "clicks": "20",
        "cpc": "1",
        "cpm": "100",
        "ctr": "10",
        "date_start": "2019-04-29",
        "date_stop": "2019-05-28",
        "frequency": "0",
        "impressions": "200",
        "objective": "LINK_CLICKS",
        "reach": "0",
        "social_spend": "20",
        "spend": "20",
        "unique_clicks": "0"
    }
    "unfound_fields": [
        "action_values",
        "actions",
        "ad_id",
        "ad_name",
        "adset_id",
        "adset_name",
        "app_store_clicks",
        "canvas_avg_view_percent",
        "canvas_avg_view_time",
        "cost_per_10_sec_video_view",
        "cost_per_action_type",
        "cost_per_estimated_ad_recallers",
        "cost_per_inline_link_click",
        "cost_per_inline_post_engagement",
        "cost_per_outbound_click",
        "cost_per_thruplay",
        "cost_per_unique_action_type",
        "cost_per_unique_click",
        "cost_per_unique_inline_link_click",
        "cost_per_unique_outbound_click",
        "cpp",
        "deeplink_clicks",
        "estimated_ad_recall_rate",
        "estimated_ad_recallers",
        "inline_link_click_ctr",
        "inline_link_clicks",
        "inline_post_engagement",
        "mobile_app_purchase_roas",
        "newsfeed_avg_position",
        "newsfeed_clicks",
        "newsfeed_impressions",
        "outbound_clicks",
        "outbound_clicks_ctr",
        "purchase_roas",
        "relevance_score",
        "unique_actions",
        "unique_ctr",
        "unique_impressions",
        "unique_inline_link_click_ctr",
        "unique_inline_link_clicks",
        "unique_link_clicks_ctr",
        "unique_outbound_clicks",
        "unique_outbound_clicks_ctr",
        "video_10_sec_watched_actions",
        "video_30_sec_watched_actions",
        "video_avg_percent_watched_actions",
        "video_avg_time_watched_actions",
        "video_complete_watched_actions",
        "video_p100_watched_actions",
        "video_p25_watched_actions",
        "video_p50_watched_actions",
        "video_p75_watched_actions",
        "video_p95_watched_actions",
        "video_play_actions",
        "video_thruplay_watched_actions",
        "website_clicks",
        "website_ctr",
        "website_purchase_roas"
    ],
    "unsupported_fields": [
        "app_store_clicks",
        "deeplink_clicks",
        "newsfeed_avg_position",
        "newsfeed_clicks",
        "newsfeed_impressions",
        "unique_impressions",
        "video_complete_watched_actions",
        "website_clicks"
    ],
    "url": "__REDACTED__/insights"
}
```

## Recommendations

set an environment variable `FB_ACCESS_TOKEN={your token}` in your `.bashrc` or whatever. Alternatively, you can add --access-token="{your token}" to every call if you want a super duper long command. I don't love it, but you do you boo.

 ¯\\_(ツ)_/¯
