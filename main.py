from datetime import datetime, timedelta
from json import loads, dumps
from os import environ
from sys import stderr

import click
from facebook import GraphAPI, GraphAPIError

try:
    ACCESS_TOKEN = environ['FB_ACCESS_TOKEN']
except KeyError as e:
    ACCESS_TOKEN = None


def process_request(ctx, url, post_filter, fields, output):
    """
    makes a call to url using fb client, trims the response down based on
    post_filter, and calls process_fields using the result and the rest of
    the params
    """
    if ctx.obj['verbose']:
        print(url)

    data = ctx.obj['fb'].get_object(url)

    if ctx.obj['verbose']:
        print(data)

    for field in post_filter:
        data = data[field]

    if ctx.obj['verbose']:
        print(data)

    return process_fields(data, fields, output)


def process_fields(data, fields, output):
    """
    May reduce a result down to a smaller result based on the fields passed.
    :param data: Iterable, A response body or subset from an api call.
    :param fields: String, comma separated for multiple fields, each field is a
    period separated list of sub-keys/indices. EG: thingies.0.id,thigies.1.id
    given the following data:
     {"thingies": [{"id": 1, "name": "t1"}, {"id": 2, "name": "t2"}]}
    would reduce to : {"thingies.0.id": 1, "thingies.1.id": 2}. If a single
    item is found at the end, only the value is returned.
     given the same data as above but with the filters "thingies.0" we would
     get back {"id": 1, "name": "t1"}
    :param output: Indicates we should write to standard out before returning
    """
    final = {}
    if not fields:
        final = data
    else:
        fields = fields.split(',')
        for field in fields:
            key = field
            value = data
            for f in field.split('.'):
                value = value[int(f)] if isinstance(value, list) else value[f]
            final[key] = value
        if len(final) == 1:
            final = next(iter(final.values()))
    if len(final) == 1 and isinstance(final, list):
        final = final[0]
    if output:
        print(dumps(final))
    return final


@click.group()
@click.option('--access-token', default=ACCESS_TOKEN,
              help='Your access token for the FB GraphApi')
@click.option('--output/--no-output', default=True)
@click.option('-v', '--verbose', default=False, is_flag=True)
@click.pass_context
def cli(ctx, access_token, output, verbose):
    ctx.ensure_object(dict)
    ctx.obj['fb'] = GraphAPI(access_token, version=3.2)
    ctx.obj['output'] = output
    ctx.obj['verbose'] = verbose
    ctx.obj['attempts'] = 0


class ContextManager(object):
    def __init__(self, context):
        self.context = context
        self.initial_output = self.context.obj['output']

    def __enter__(self):
        self.context.obj['output'] = False
        return self.context

    def __exit__(self, type, value, traceback):
        self.context.obj['output'] = self.initial_output


@cli.command()
@click.option('--fields')
@click.pass_context
def get_ad_account(ctx, fields):
    return process_request(ctx, 'me/?fields=adaccounts',
                           ['adaccounts', 'data'], fields, ctx.obj['output'])


@cli.command()
@click.option('--fields')
@click.pass_context
def get_ad_account_insights(ctx, fields):
    with ContextManager(ctx) as c:
        account_id = c.invoke(get_ad_account, fields='0.id')
    query_fields = [
        'account_id', 'account_name', 'account_currency', 'clicks', 'cpc',
        'cpm', 'ctr', 'frequency', 'impressions', 'reach', 'social_spend',
        'spend', 'unique_clicks',
    ]
    return process_request(
        ctx,
        f'{account_id}/insights?fields=' + ','.join(query_fields),
        ['data'], fields, ctx.obj['output']
    )


@cli.command()
@click.option('--campaign-id')
@click.option('--fields')
@click.pass_context
def get_campaign_insights(ctx, campaign_id, fields):
    with ContextManager(ctx) as c:
        account_id = c.invoke(get_ad_account, fields='0.id')
        if not campaign_id:
            campaigns = c.invoke(get_campaigns, account_id=account_id)
            if not isinstance(campaigns, list):
                campaigns = [campaigns]
            campaign_id = select_option(campaigns, 'name', 'Select a campaign',
                                        'campaign')['id']
    return process_request(ctx, f'{campaign_id}/insights',
                           ['data'],
                           fields, ctx.obj['output'])


@cli.command()
@click.option('--fields')
@click.pass_context
def get_campaigns(ctx, fields, account_id=None):
    if not account_id:
        with ContextManager(ctx) as c:
            account_id = c.invoke(get_ad_account, fields='0.id')
    return process_request(ctx, f'{account_id}/campaigns?fields=id,name',
                           ['data'],
                           fields, ctx.obj['output'])


@cli.command()
@click.option('--fields')
@click.pass_context
def get_adsets(ctx, fields):
    with ContextManager(ctx) as c:
        account_id = c.invoke(get_ad_account, fields='0.id')
    return process_request(
        ctx,
        f'{account_id}/adsets?fields=id,name',
        ['data'],
        fields,
        ctx.obj['output']
    )


@cli.command()
@click.option('--fields')
@click.pass_context
def get_adimages(ctx, fields):
    with ContextManager(ctx) as c:
        account_id = c.invoke(get_ad_account, fields='0.id')
    return process_request(ctx,
                           f'{account_id}/adimages?fields=hash,id,url',
                           ['data'], fields, ctx.obj['output'])


@cli.command()
@click.option('--fields')
@click.pass_context
def get_ads(ctx, fields):
    with ContextManager(ctx) as c:
        account_id = c.invoke(get_ad_account, fields='0.id')
    return process_request(ctx, f'{account_id}/ads', ['data'], fields,
                           ctx.obj['output'])


@cli.command()
@click.option('--fields')
@click.pass_context
def get_adcreatives(ctx, fields):
    with ContextManager(ctx) as c:
        account_id = c.invoke(get_ad_account, fields='0.id')
    return process_request(ctx,
                           f'{account_id}/adcreatives',
                           ['data'], fields, ctx.obj['output'])


def create_object(fb, url, definition, output, files=None):
    result = fb.request(url, method='POST', post_args=definition, files=files)
    if output:
        print(result)

    return result


@cli.command()
@click.option('--definition', default={},
              help='json string representing the campaign')
@click.pass_context
def create_campaign(ctx, definition):
    with ContextManager(ctx) as c:
        account_id = c.invoke(get_ad_account, fields='0.id')
    definition = loads(definition)
    default = {
        "objective": "LINK_CLICKS",
        "status": "PAUSED"
    }
    default.update(definition)
    for field in ['name']:
        if field not in definition:
            raise Exception(f'You must provide a {field} for your adset')
    return create_object(ctx.obj['fb'], f'{account_id}/campaigns',
                         definition, ctx.obj['output'])


@cli.command()
@click.option('--definition', default={},
              help='json string representing the adset')
@click.pass_context
def create_adset(ctx, definition):
    with ContextManager(ctx) as c:
        account_id = c.invoke(get_ad_account, fields='0.id')
    definition = loads(definition)
    default = {
        "billing_event": "IMPRESSIONS",
        "bid_amount": 100,
        "daily_budget": 1000,
        "targeting": {
            "geo_locations": {
                "countries": ["US"]
            },
            "publisher_platforms": ["facebook"]
        },
        "start_time": datetime.now().isoformat(),
        "end_time": (datetime.now() + timedelta(days=300)).isoformat(),
        "optimization_goal": "REACH"
    }
    default.update(definition)
    for field in ['name', 'campaign_id']:
        if field not in definition:
            raise Exception(f'You must provide a {field} for your adset')
    return create_object(ctx.obj['fb'], f'{account_id}/adsets',
                         definition, ctx.obj['output'])


@cli.command()
@click.option('--image', help='path to your image')
@click.pass_context
def create_adimage(ctx, image):
    with ContextManager(ctx) as c:
        account_id = c.invoke(get_ad_account, fields='0.id')
    with open(image, 'rb') as f:
        return create_object(
            ctx.obj['fb'],
            f'{account_id}/adimages',
            None,
            ctx.obj['output'],
            files={'filename': f}
        )


@cli.command()
@click.option('--page-id', help='Facebook Page ID')
@click.option('--name', help='The name for this creative')
@click.option('--image-hash')
@click.option('--image-url')
@click.option('--image-message')
@click.pass_context
def create_adcreative(ctx, page_id, name, image_hash, image_url,
                      image_message):
    with ContextManager(ctx) as c:
        account_id = c.invoke(get_ad_account, fields='0.id')
    try:
        if not image_hash or not image_url:
            image = select_image(ctx)
            image_hash = image['hash']
            image_url = image['url']

        while not page_id:
            page_id = select_page()

        return create_object(
            ctx.obj['fb'],
            f'{account_id}/adcreatives',
            {
                'name': name,
                'object_story_spec': {
                    'link_data': {
                        "image_hash": image_hash,
                        "link": image_url,
                        "message": image_message or "Default message"
                    },
                    'page_id': page_id
                }
            },
            ctx.obj['output']
        )
    except Exception as e:
        print(e)


@cli.command()
@click.option('--status')
@click.option('--creative_id')
@click.option('--adset_id')
@click.option('--name')
@click.pass_context
def create_ad(ctx, status, creative_id, adset_id, name):
    with ContextManager(ctx) as c:
        account_id = c.invoke(get_ad_account, fields='0.id')
    status = status or 'ACTIVE'
    try:
        adset_id = adset_id or select_adset(ctx)
        creative = {
            'creative_id': creative_id or select_creative(ctx)
        }
        return create_object(ctx.obj['fb'], f'{account_id}/ads', {
            'name': name or 'DEFAULT AD NAME',
            'status': status,
            'creative': creative,
            'adset_id': adset_id
        }, ctx.obj['output'])
    except Exception as e:
        print(e)


def select_creative(ctx):
    creatives = ctx.invoke(get_adcreatives, output=False)
    return select_option(creatives, 'name', 'Select a creative', 'creative')


def select_image(ctx):
    images = ctx.invoke(get_adimages, output=False)
    return select_option(images, 'url', 'Which image would you like to use?',
                         'image')


def select_adset(ctx):
    adsets = ctx.invoke(get_adsets, output=False)
    return select_option(adsets, 'name', 'Which adset would you like to '
                                         'use?', 'adset')


def select_option(options, display_field, prompt, element):
    if len(options) < 1:
        raise Exception(f'No {element} available to select.')
    if len(options) == 1:
        return options[0]
    index = 0
    while index < 1:
        c = 0
        for option in options:
            c += 1
            print(f'{c}) {option[display_field]}')
        index = click.prompt(f'{prompt} (1-{c})', type=int)
        if index not in range(1, c):
            index = 0

    return options[index]


def select_page():
    return click.prompt('Yeah, so FB will not tell me what pages are '
                        'available given an ad Account Owner\'s access token '
                        'sooooo, look up a fb page id like a suckah and type '
                        'it in here... suckah!')


@cli.command()
@click.option('--fields')
@click.option('--url')
@click.option('--filter')
@click.option('--object-ids', default={})
@click.pass_context
def call_gql(ctx, fields, url, object_ids, filter, output=True):
    """
    example: python main.py call-gql --url='{campaign_id}/insights' \
      --fields="..." --filter='["data"]'
      fields can be a gigantic comma separated string listing of all the fields
      that could possibly exist
      --filter just simplifies the output
      acceptable fstrings in url are: {'campaign_id', 'account_id', 'adset_id',
      'ad_id'} which will use the specific subcommand to pull the first id
      for that object type and perform a replacement.

    output:
    {
        "unsupported_fields": [/* fields which gave back an error */],
        "unfound_fields": [/* fields weren't returned, no error caused */],
        "found_fields": [/* fields you should see in result*/]
        "result": {/* the fields and values found in the response */}
    }

    """
    if ctx.obj['attempts'] > 3:
        raise Exception('Too many attempts, aborting')

    lookups = {
        'campaign_id': get_campaigns,
        'account_id': get_ad_account,
        'adset_id': get_adsets,
        'ad_id': get_ads,
        'adcreative_id': get_adcreatives,
    }
    for id_type, call in lookups.items():
        with ContextManager(ctx) as c:
            if '{' + id_type + '}' in url and id_type not in object_ids:
                r = c.invoke(call)
                if 'id' in r:
                    object_ids[id_type] = r['id']
                elif isinstance(r, list) and r:
                    object_ids[id_type] = r[0]['id']
                else:
                    raise Exception(f'Could not replace {id_type} by lookup')
    url = url.format(**object_ids)
    join = '&' if '?' in url else '?'
    printable = {'unsupported_fields': []}
    try:
        result = process_request(ctx, f'{url}{join}fields={fields}',
                                 loads(filter) or [], [],
                                 output=False)
    except GraphAPIError as e:
        err = e.result['error']
        if err['code'] == 100 and 'error_subcode' not in err:
            msg = err['message']
            msg = msg[7:msg.find(' are not valid for fields param.')]
            unsupported_fields = set(msg.split(', '))
            supported_fields = set(fields.split(','))\
                .difference(unsupported_fields)
            printable['unsupported_fields'] = sorted(list(unsupported_fields))
            print('reattempting request with supported_fields', file=stderr)
            ctx.obj['attempts'] += 1
            result = ctx.invoke(call_gql, fields=','.join(supported_fields),
                                url=url, object_ids=object_ids,
                                filter=filter, output=False)
        else:
            raise

    if isinstance(result, dict):
        found_set = set(result.keys())
        fields_set = set(fields.split(','))
        unfound_set = fields_set.difference(found_set)
        unfound = sorted(list(unfound_set))
        printable['unfound_fields'] = unfound
    printable['result'] = result
    printable['url'] = url
    printable['object_ids'] = object_ids
    if output:
        print(
            dumps(printable, sort_keys=True, indent=4, separators=(',', ': '))
        )
    return result


if __name__ == '__main__':
    cli()
