#!/usr/bin/env python3
import json, re, sys, subprocess, urllib.parse, urllib.request, http.cookiejar, time, os, socket, datetime
from pathlib import Path
BEARER=os.environ.get('X_SIGNAL_BEARER')
UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'

FEATURES_TIMELINE={
 'rweb_video_screen_enabled': False,'profile_label_improvements_pcf_label_in_post_enabled': True,
 'rweb_tipjar_consumption_enabled': True,'verified_phone_label_enabled': False,
 'creator_subscriptions_tweet_preview_api_enabled': True,'responsive_web_graphql_timeline_navigation_enabled': True,
 'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,'premium_content_api_read_enabled': False,
 'communities_web_enable_tweet_community_results_fetch': True,'c9s_tweet_anatomy_moderator_badge_enabled': True,
 'responsive_web_grok_analyze_button_fetch_trends_enabled': False,'responsive_web_grok_analyze_post_followups_enabled': True,
 'responsive_web_jetfuel_frame': False,'responsive_web_grok_share_attachment_enabled': True,'articles_preview_enabled': True,
 'responsive_web_edit_tweet_api_enabled': True,'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
 'view_counts_everywhere_api_enabled': True,'longform_notetweets_consumption_enabled': True,
 'responsive_web_twitter_article_tweet_consumption_enabled': True,'tweet_awards_web_tipping_enabled': False,
 'responsive_web_grok_show_grok_translated_post': False,'responsive_web_grok_analysis_button_from_backend': False,
 'creator_subscriptions_quote_tweet_preview_enabled': False,'freedom_of_speech_not_reach_fetch_enabled': True,
 'standardized_nudges_misinfo': True,'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
 'longform_notetweets_rich_text_read_enabled': True,'longform_notetweets_inline_media_enabled': True,
 'responsive_web_grok_image_annotation_enabled': True,'responsive_web_enhance_cards_enabled': False}
FEATURES_BOOKMARK={
 'rweb_video_screen_enabled': False,'profile_label_improvements_pcf_label_in_post_enabled': True,'responsive_web_profile_redirect_enabled': False,
 'rweb_tipjar_consumption_enabled': False,'verified_phone_label_enabled': False,'creator_subscriptions_tweet_preview_api_enabled': True,
 'responsive_web_graphql_timeline_navigation_enabled': True,'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
 'premium_content_api_read_enabled': False,'communities_web_enable_tweet_community_results_fetch': True,'c9s_tweet_anatomy_moderator_badge_enabled': True,
 'articles_preview_enabled': True,'responsive_web_edit_tweet_api_enabled': True,'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
 'view_counts_everywhere_api_enabled': True,'longform_notetweets_consumption_enabled': True,'responsive_web_twitter_article_tweet_consumption_enabled': True,
 'tweet_awards_web_tipping_enabled': False,'content_disclosure_indicator_enabled': True,'content_disclosure_ai_generated_indicator_enabled': True,
 'freedom_of_speech_not_reach_fetch_enabled': True,'standardized_nudges_misinfo': True,'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
 'longform_notetweets_rich_text_read_enabled': True,'longform_notetweets_inline_media_enabled': False,'responsive_web_enhance_cards_enabled': False}
FEATURES_LIKES={**FEATURES_BOOKMARK,'responsive_web_grok_analyze_post_followups_enabled': True,'responsive_web_jetfuel_frame': True,'responsive_web_grok_share_attachment_enabled': True,'responsive_web_grok_annotations_enabled': True,'responsive_web_grok_analysis_button_from_backend': True,'post_ctas_fetch_enabled': False,'responsive_web_grok_image_annotation_enabled': True,'responsive_web_grok_imagine_annotation_enabled': True,'responsive_web_grok_community_note_auto_translation_is_enabled': False}
FEATURES_USER={
 'hidden_profile_subscriptions_enabled': True,'rweb_tipjar_consumption_enabled': True,'responsive_web_graphql_exclude_directive_enabled': True,
 'verified_phone_label_enabled': False,'subscriptions_verification_info_is_identity_verified_enabled': True,
 'subscriptions_verification_info_verified_since_enabled': True,'highlights_tweets_tab_ui_enabled': True,
 'responsive_web_twitter_article_notes_tab_enabled': True,'subscriptions_feature_can_gift_premium': True,
 'creator_subscriptions_tweet_preview_api_enabled': True,'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
 'responsive_web_graphql_timeline_navigation_enabled': True}
FALLBACK={'Bookmarks':'Fy0QMy4q_aZCpkO0PnyLYw','HomeTimeline':'c-CzHF1LboFilMpsx4ZCrQ','HomeLatestTimeline':'BKB7oi212Fi7kQtCBGE4zA','Likes':'RozQdCp4CilQzrcuU0NY5w','UserByScreenName':'qRednkZG-rn1P6b48NINmQ','UserTweets':'q6xj5bs0hapm9309hexA_g'}

def load_cookies():
    import browser_cookie3
    errors=[]
    for loader_name in ['chrome','chromium','brave','safari']:
        loader=getattr(browser_cookie3, loader_name, None)
        if not loader: continue
        try:
            cj=loader(domain_name='.x.com')
            names={c.name for c in cj}
            if 'ct0' in names and ('auth_token' in names or any(c.name=='twid' for c in cj)):
                return cj, loader_name
            errors.append(f'{loader_name}: cookies {sorted(list(names))[:10]}')
        except Exception as e:
            errors.append(f'{loader_name}: {type(e).__name__}: {e}')
    raise RuntimeError('no usable x.com cookies; '+ ' | '.join(errors))

def cookie_value(cj, name):
    for c in cj:
        if c.name==name: return c.value
    return None

def resolve_ids():
    try:
        data=json.load(urllib.request.urlopen('https://raw.githubusercontent.com/fa0311/twitter-openapi/refs/heads/main/src/config/placeholder.json', timeout=10))
        return {k: data.get(k,{}).get('queryId') or v for k,v in FALLBACK.items()}
    except Exception:
        return FALLBACK.copy()

def api(cj, path, method='GET', data=None):
    if not BEARER:
        return {'_error': 'missing X_SIGNAL_BEARER'}
    ct0=cookie_value(cj,'ct0')
    opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    url='https://x.com'+path
    body=None
    headers={'Authorization':'Bearer '+BEARER,'X-Csrf-Token':ct0,'X-Twitter-Auth-Type':'OAuth2Session','X-Twitter-Active-User':'yes','User-Agent':UA,'Accept':'*/*','Referer':'https://x.com/home','Content-Type':'application/json'}
    if data is not None:
        body=json.dumps(data,separators=(',',':')).encode()
    req=urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with opener.open(req, timeout=float(os.environ.get('X_SIGNAL_TIMEOUT', '12'))) as r:
            raw=r.read().decode('utf-8','replace')
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        txt=e.read().decode('utf-8','replace')[:500]
        return {'_error': e.code, '_body': txt, '_path': path[:160]}
    except (socket.timeout, TimeoutError) as e:
        return {'_error': 'timeout', '_body': str(e), '_path': path[:160]}
    except Exception as e:
        return {'_error': type(e).__name__, '_body': str(e)[:500], '_path': path[:160]}

def qparams(variables, features):
    return 'variables='+urllib.parse.quote(json.dumps(variables,separators=(',',':')))+'&features='+urllib.parse.quote(json.dumps(features,separators=(',',':')))

def extract_tweet(result, seen):
    if not result or not isinstance(result,dict): return None
    tw=result.get('tweet') or result
    if tw.get('__typename')=='TweetWithVisibilityResults': tw=tw.get('tweet') or tw
    if not tw.get('rest_id') or tw.get('rest_id') in seen: return None
    legacy=tw.get('legacy') or {}
    text=((tw.get('note_tweet') or {}).get('note_tweet_results') or {}).get('result',{}).get('text') or legacy.get('full_text') or ''
    user=((tw.get('core') or {}).get('user_results') or {}).get('result') or {}
    uleg=user.get('legacy') or {}
    screen=uleg.get('screen_name') or (user.get('core') or {}).get('screen_name') or 'unknown'
    name=uleg.get('name') or (user.get('core') or {}).get('name') or ''
    seen.add(tw['rest_id'])
    ents=legacy.get('entities') or {}
    expanded=[u.get('expanded_url') for u in ents.get('urls',[]) if u.get('expanded_url')]
    media=[]
    for m in ((legacy.get('extended_entities') or {}).get('media') or ents.get('media') or []):
        media.append({'type':m.get('type'), 'url':m.get('expanded_url') or m.get('media_url_https')})
    return {'id':tw['rest_id'],'author':screen,'name':name,'text':text,'likes':legacy.get('favorite_count') or 0,'retweets':legacy.get('retweet_count') or 0,'replies':legacy.get('reply_count') or 0,'views':int((tw.get('views') or {}).get('count') or 0),'created_at':legacy.get('created_at') or '', 'url':f'https://x.com/{screen}/status/{tw["rest_id"]}', 'expanded_urls':expanded, 'media':media}

def parse_entries(instructions, seen):
    tweets=[]; cursor=None
    for inst in instructions or []:
        entries=inst.get('entries') or []
        # some AddEntries nested in inst['entry']? ignore
        for entry in entries:
            c=entry.get('content') or {}
            if c.get('entryType')=='TimelineTimelineCursor' or c.get('__typename')=='TimelineTimelineCursor' or entry.get('entryId','').startswith(('cursor-bottom-','cursor-showMore-')):
                if c.get('cursorType') in ('Bottom','ShowMore') or 'cursor-bottom-' in entry.get('entryId','') or 'cursor-showMore-' in entry.get('entryId',''):
                    cursor=c.get('value') or ((c.get('itemContent') or {}).get('value')) or cursor
                continue
            res=((c.get('itemContent') or {}).get('tweet_results') or {}).get('result')
            tw=extract_tweet(res, seen)
            if tw: tweets.append(tw)
            for item in c.get('items') or []:
                res=((((item.get('item') or {}).get('itemContent') or {}).get('tweet_results') or {}).get('result'))
                tw=extract_tweet(res, seen)
                if tw: tweets.append(tw)
    return tweets, cursor

def fetch_bookmarks(cj, ids, limit=25):
    seen=set(); all=[]; cursor=None; err=None
    for _ in range(5):
        variables={'count':min(100,limit-len(all)+10),'includePromotedContent':False}
        if cursor: variables['cursor']=cursor
        path=f'/i/api/graphql/{ids["Bookmarks"]}/Bookmarks?'+qparams(variables, FEATURES_BOOKMARK)
        d=api(cj,path)
        if d.get('_error'): err=d; break
        inst=(((d.get('data') or {}).get('bookmark_timeline_v2') or {}).get('timeline') or {}).get('instructions') or (((d.get('data') or {}).get('bookmark_timeline') or {}).get('timeline') or {}).get('instructions') or []
        tws,cursor=parse_entries(inst, seen); all+=tws
        if len(all)>=limit or not cursor: break
    return all[:limit], err

def fetch_timeline(cj, ids, typ='for-you', limit=30):
    endpoint='HomeTimeline' if typ=='for-you' else 'HomeLatestTimeline'; method='GET' if typ=='for-you' else 'POST'
    seen=set(); all=[]; cursor=None; err=None
    for _ in range(5):
        variables={'count':min(40,limit-len(all)+8),'includePromotedContent':False,'latestControlAvailable':True,'requestContext':'launch'}
        if typ=='for-you': variables['withCommunity']=True
        else: variables['seenTweetIds']=[]
        if cursor: variables['cursor']=cursor
        path=f'/i/api/graphql/{ids[endpoint]}/{endpoint}?'+qparams(variables, FEATURES_TIMELINE)
        if method=='POST':
            # X currently expects variables/features in query string for this op; empty json body is accepted in some builds, but use body params for POST fallback if needed.
            d=api(cj,path,method='POST',data={})
        else:
            d=api(cj,path)
        if d.get('_error') and method=='POST':
            d=api(cj,path,method='GET')
        if d.get('_error'): err=d; break
        inst=(((d.get('data') or {}).get('home') or {}).get('home_timeline_urt') or {}).get('instructions') or []
        tws,cursor=parse_entries(inst, seen); all+=tws
        if len(all)>=limit or not cursor: break
    return all[:limit], err


def resolve_user_id(cj, ids, username):
    variables = {'screen_name': username, 'withSafetyModeUserFields': True}
    path = f'/i/api/graphql/{ids["UserByScreenName"]}/UserByScreenName?' + qparams(variables, FEATURES_USER)
    d = api(cj, path)
    if d.get('_error'):
        return None, d
    user_id = (((d.get('data') or {}).get('user') or {}).get('result') or {}).get('rest_id')
    if not user_id:
        return None, {'_error': 'no user id'}
    return str(user_id), None


def fetch_user_tweets(cj, ids, username, limit=15):
    user_id, err = resolve_user_id(cj, ids, username)
    if err:
        return [], err
    seen = set()
    all_tweets = []
    cursor = None
    err = None
    for _ in range(4):
        variables = {
            'userId': user_id,
            'count': min(40, limit - len(all_tweets) + 8),
            'includePromotedContent': False,
            'withQuickPromoteEligibilityTweetFields': True,
            'withVoice': True,
        }
        if cursor:
            variables['cursor'] = cursor
        path = f'/i/api/graphql/{ids["UserTweets"]}/UserTweets?' + qparams(variables, FEATURES_TIMELINE)
        d = api(cj, path)
        if d.get('_error'):
            err = d
            break
        user = ((d.get('data') or {}).get('user') or {}).get('result') or {}
        inst = ((user.get('timeline_v2') or {}).get('timeline') or {}).get('instructions') or ((user.get('timeline') or {}).get('timeline') or {}).get('instructions') or []
        tweets, cursor = parse_entries(inst, seen)
        all_tweets += tweets
        if len(all_tweets) >= limit or not cursor:
            break
    return all_tweets[:limit], err

def detect_user(cj, ids):
    # Try home page html for screen name, fallback twid user id only
    try:
        opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        req=urllib.request.Request('https://x.com/home', headers={'User-Agent':UA})
        txt=opener.open(req,timeout=float(os.environ.get('X_SIGNAL_TIMEOUT', '12'))).read().decode('utf-8','replace')
        m=re.search(r'"screen_name":"([A-Za-z0-9_]+)"', txt)
        if m: return m.group(1), None
    except Exception: pass
    return None, cookie_value(cj,'twid')

def fetch_likes(cj, ids, username=None, user_id=None, limit=20):
    err=None
    if not user_id:
        if not username: return [], {'_error':'no username'}
        variables={'screen_name':username,'withSafetyModeUserFields':True}
        path=f'/i/api/graphql/{ids["UserByScreenName"]}/UserByScreenName?'+qparams(variables, FEATURES_USER)
        d=api(cj,path)
        if d.get('_error'): return [], d
        user_id=(((d.get('data') or {}).get('user') or {}).get('result') or {}).get('rest_id')
        if not user_id: return [], {'_error':'no user id'}
    seen=set(); all=[]; cursor=None
    for _ in range(5):
        variables={'userId':str(user_id).strip('u='),'count':min(100,limit-len(all)+10),'includePromotedContent':False,'withClientEventToken':False,'withBirdwatchNotes':False,'withVoice':True}
        if cursor: variables['cursor']=cursor
        path=f'/i/api/graphql/{ids["Likes"]}/Likes?'+qparams(variables, FEATURES_LIKES)
        d=api(cj,path)
        if d.get('_error'): err=d; break
        user=((d.get('data') or {}).get('user') or {}).get('result') or {}
        inst=((user.get('timeline_v2') or {}).get('timeline') or {}).get('instructions') or ((user.get('timeline') or {}).get('timeline') or {}).get('instructions') or []
        tws,cursor=parse_entries(inst, seen); all+=tws
        if len(all)>=limit or not cursor: break
    return all[:limit], err

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / 'config' / 'x_users.toml'
CHANNELS = ('bookmarks', 'for_you', 'following', 'likes')
FETCH_DEPTH_LIMIT = 50


def parse_user_config(text):
    users = []
    current = None
    for raw_line in text.splitlines():
        line = raw_line.split('#', 1)[0].strip()
        if not line:
            continue
        if line == '[[users]]':
            if current:
                users.append(current)
            current = {}
            continue
        if current is None or '=' not in line:
            continue
        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip().strip('\"').strip("'")
        current[key] = value
    if current:
        users.append(current)
    return users


def load_users(config_path=DEFAULT_CONFIG_PATH):
    if not config_path.exists():
        return [{'username': 'tangyuanjc', 'role': 'owner'}]
    users = []
    seen = set()
    for item in parse_user_config(config_path.read_text(encoding='utf-8')):
        username = str(item.get('username', '')).strip().lstrip('@')
        if not username or username.lower() in seen:
            continue
        role = str(item.get('role', 'kol')).strip() or 'kol'
        seen.add(username.lower())
        users.append({'username': username, 'role': role})
    return users or [{'username': 'tangyuanjc', 'role': 'owner'}]


def with_source_user(tweets, username):
    enriched = []
    for tweet in tweets:
        item = dict(tweet)
        item['source_user'] = username
        enriched.append(item)
    return enriched


def empty_counts():
    return {channel: {'total': 0, 'by_user': {}} for channel in CHANNELS}


def add_channel(out, counts, channel, username, tweets):
    enriched = with_source_user(tweets, username)
    out[channel].extend(enriched)
    counts[channel]['by_user'][username] = len(enriched)
    counts[channel]['total'] += len(enriched)


def fetch_owner_channels(cj, ids, username, twid):
    bookmarks, e_b = fetch_bookmarks(cj, ids, FETCH_DEPTH_LIMIT)
    foryou, e_f = fetch_timeline(cj, ids, 'for-you', FETCH_DEPTH_LIMIT)
    following, e_fl = fetch_timeline(cj, ids, 'following', FETCH_DEPTH_LIMIT)
    likes, e_l = fetch_likes(cj, ids, username=username, user_id=twid, limit=FETCH_DEPTH_LIMIT)
    return {
        'bookmarks': (bookmarks, e_b),
        'for_you': (foryou, e_f),
        'following': (following, e_fl),
        'likes': (likes, e_l),
    }


def fetch_kol_channels(cj, ids, username):
    tweets, tweets_err = fetch_user_tweets(cj, ids, username=username, limit=FETCH_DEPTH_LIMIT)
    likes, likes_err = [], {'_skipped': 'kol likes disabled for cron budget'}
    return {
        'bookmarks': ([], {'_skipped': 'auth account only'}),
        'for_you': ([], {'_skipped': 'auth account only'}),
        'following': (tweets, tweets_err),
        'likes': (likes, likes_err),
    }


def compact_error(err):
    if not err:
        return None
    if isinstance(err, dict):
        return {k: err.get(k) for k in ('_error', '_body', '_path', '_skipped') if k in err}
    return {'_error': str(err)}


def main():
    users = load_users()
    cj, browser = load_cookies()
    ids = resolve_ids()
    detected_username, twid = detect_user(cj, ids)

    out = {
        'ok': True,
        'browser_cookie_source': browser,
        'username': detected_username,
        'twid_present': bool(twid),
        'configured_users': users,
        'query_ids': ids,
        'counts': empty_counts(),
        'errors': {},
        'bookmarks': [],
        'for_you': [],
        'following': [],
        'likes': [],
    }

    owner_seen = False
    for user in users:
        username = user['username']
        role = user.get('role') or 'kol'
        is_owner = role == 'owner' or (detected_username and username.lower() == detected_username.lower())
        try:
            channels = fetch_owner_channels(cj, ids, detected_username or username, twid) if is_owner and not owner_seen else fetch_kol_channels(cj, ids, username)
            if is_owner:
                owner_seen = True
            out['errors'][username] = {}
            for channel, (tweets, err) in channels.items():
                add_channel(out, out['counts'], channel, username, tweets)
                compacted = compact_error(err)
                if compacted:
                    out['errors'][username][channel] = compacted
        except Exception as exc:
            out['errors'][username] = {'_error': type(exc).__name__, '_body': str(exc)[:500]}
            continue

    if not owner_seen:
        fallback_username = detected_username or 'tangyuanjc'
        try:
            channels = fetch_owner_channels(cj, ids, detected_username, twid)
            out['errors'].setdefault(fallback_username, {})
            for channel, (tweets, err) in channels.items():
                add_channel(out, out['counts'], channel, fallback_username, tweets)
                compacted = compact_error(err)
                if compacted:
                    out['errors'][fallback_username][channel] = compacted
        except Exception as exc:
            out['errors'][fallback_username] = {'_error': type(exc).__name__, '_body': str(exc)[:500]}

    out['generated_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    out['generated_at_local'] = datetime.datetime.now().isoformat()
    latest_path = Path.home() / '.hermes' / 'tmp' / 'x_signal_sync_latest.json'
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = latest_path.with_suffix('.json.tmp')
    with tmp_path.open('w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write('\n')
    tmp_path.replace(latest_path)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
