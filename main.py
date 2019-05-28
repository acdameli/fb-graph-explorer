from datetime import datetime, timedelta
from json import loads
from os import environ

import click
from facebook import GraphAPI

try:
    ACCESS_TOKEN = environ['FB_ACCESS_TOKEN']
except KeyError as e:
    ACCESS_TOKEN = None


def process_request(fb, url, post_filter, fields, output):
    """
    makes a call to url using fb client, trims the response down based on
    post_filter, and calls process_fields using the result and the rest of
    the params
    :param fb:
    :param url:
    :param post_filter:
    :param fields:
    :param output:
    :return:
    """
    data = fb.get_object(url)
    for field in post_filter:
        data = data[field]
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
    if output:
        print(final)
    return final


@click.group()
@click.option('--access-token', default=ACCESS_TOKEN,
              help='Your access token for the FB GraphApi')
@click.pass_context
def cli(ctx, access_token):
    ctx.ensure_object(dict)
    ctx.obj['fb'] = GraphAPI(access_token, version=3.2)


@cli.command()
@click.pass_context
def get_ad_account(ctx, fields, output=True):
    return process_request(ctx.obj['fb'], 'me/?fields=adaccounts',
                           ['adaccounts', 'data'], fields, output)


@cli.command()
@click.option('--fields')
@click.pass_context
def get_campaigns(ctx, fields, output=True):
    account_id = ctx.invoke(get_ad_account, fields='0.id', output=False)
    return process_request(ctx.obj['fb'], f'{account_id}/campaigns', ['data'],
                           fields, output)


@cli.command()
@click.option('--fields')
@click.pass_context
def get_adsets(ctx, fields, output=True):
    account_id = ctx.invoke(get_ad_account, fields='0.id', output=False)
    return process_request(
        ctx.obj['fb'],
        f'{account_id}/adsets?fields=id,name',
        ['data'],
        fields,
        output
    )


@cli.command()
@click.option('--fields')
@click.pass_context
def get_adimages(ctx, fields, output=True):
    account_id = ctx.invoke(get_ad_account, fields='0.id', output=False)
    return process_request(ctx.obj['fb'],
                           f'{account_id}/adimages?fields=hash,id,url',
                           ['data'], fields, output)


@cli.command()
@click.option('--fields')
@click.pass_context
def get_ads(ctx, fields, output=True):
    account_id = ctx.invoke(get_ad_account, fields='0.id', output=False)
    return process_request(ctx.obj['fb'], f'{account_id}/ads', ['data'], fields,
                           output)


@cli.command()
@click.option('--fields')
@click.pass_context
def get_adcreatives(ctx, fields, output=True):
    account_id = ctx.invoke(get_ad_account, fields='0.id', output=False)
    return process_request(ctx.obj['fb'],
                           f'{account_id}/adcreatives',
                           ['data'], fields, output)


def create_object(fb, url, definition, output, files=None):
    result = fb.request(url, method='POST', post_args=definition, files=files)
    if output:
        print(result)

    return result


@cli.command()
@click.option('--definition', default={},
              help='json string representing the campaign')
@click.pass_context
def create_campaign(ctx, definition, output=True):
    account_id = ctx.invoke(get_ad_account, fields='0.id', output=False)
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
                         definition, output)


@cli.command()
@click.option('--definition', default={},
              help='json string representing the adset')
@click.pass_context
def create_adset(ctx, definition, output=True):
    account_id = ctx.invoke(get_ad_account, fields='0.id', output=False)
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
                         definition, output)


@cli.command()
@click.option('--image', help='path to your image')
@click.pass_context
def create_adimage(ctx, image, output=True):
    account_id = ctx.invoke(get_ad_account, fields='0.id', output=False)
    with open(image, 'rb') as f:
        return create_object(
            ctx.obj['fb'],
            f'{account_id}/adimages',
            None,
            output,
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
                      image_message, output=True):
    account_id = ctx.invoke(get_ad_account, fields='0.id', output=False)
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
            output
        )
    except Exception as e:
        print(e)


@cli.command()
@click.option('--status')
@click.option('--creative_id')
@click.option('--adset_id')
@click.option('--name')
@click.pass_context
def create_ad(ctx, status, creative_id, adset_id, name, output=True):
    account_id = ctx.invoke(get_ad_account, fields='0.id', output=False)
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
        }, output)
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


if __name__ == '__main__':
    cli()
