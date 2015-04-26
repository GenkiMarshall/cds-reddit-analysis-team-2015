#! /bin/python2

import time
import requests

# -- api notes --
# https://www.reddit.com/dev/api
# fullname = type + id (note that reddit doesn't follow this convention consistently)
# link = a post with a comment section
# comment = comment

header = {'user-agent': 'part two user agent'} # required for rate limiting
BASE_URL = 'http://www.reddit.com'
COMMENT_EX_1 = 'cq7t7ka' # a top-level comment
COMMENT_EX_2 = 'cq7vl6s' # a reply to a top-level comment


# OTHER HELPERS

# creates a url
def make_url(*args):
    ret = ''
    for add in args:
        if ret == '':
            ret = add
        elif ret[-1:] == '/':
            ret += add
        else:
            ret += '/' + add
    return ret + '.json'

# takes in a fullname of a thing 'tn_abc...' and returns n == 3
def is_link_name(fullname): return fullname[1:2] == '3'

# takes in a fullname of a thing 'tn_abc...' and returns its id 'abc...'
def rm_type(fullname): return fullname[3:]

# returns the replies to the given link or comment
def get_replies(data, is_link):
    ret = data[1]['data']['children']
    if not is_link: ret = ret[0]['data']['replies']['data']['children']
    return ret

# returns the main data for a given JSON return object
# section = 0 for link, 1 for comment
def get_meta_data(data, section): return data[section]['data']['children'][0]['data']

# takes in a link fullname of form "t3_31y53t" and returns the link url itself
def get_url_from_fullname(fullname):
    link_id = rm_type(fullname)
    r = requests.get(make_url(BASE_URL, link_id), headers=header)
    return r.url[:-6]

# IMPL HELPERS

# iterates through all direct replies to given parent to find ...
# the number of direct replies before created_utc
# does the comment_tree looper
# base_link_id is something of form 't3_31y53t'
# parent_fullname is something of form 't{3,1}_cq7t7ka'
def get_num_prior_replies(base_link_id, parent_fullname, orig_utc):

    # helper for when finds 'more' objects
    # checks if the comment of the given comment_id was posted before orig_utc
    def check_if_earlier(comment_id):
        data = requests.get(make_url(base_link, comment_id), headers=header).json()
        return get_meta_data(data, 1)['created_utc'] < orig_utc

    # comment_tree has the given parent as the root
    def gnpr_helper(comment_tree):
        num_prior_replies = 0
        for comment in comment_tree:
            data = comment['data']
            if comment['kind'] == 'more':
                # these 'more' objects contain more comments to iterate through
                children = data['children']
                children_len = len(children)
                print('found a more-object with ' + `children_len` + ' children...')
                if children_len > 10:
                    print('this is too many to iterate, so only the first ten will be checked')
                for idx,c in enumerate(children):
                    if idx < 10:
                        print('checking more-child #' + `idx+1` + '...')
                        time.sleep(2)
                        if check_if_earlier(c): num_prior_replies += 1
            else:
                curr_utc = data['created_utc']
                if curr_utc < orig_utc: num_prior_replies += 1
        return num_prior_replies

    parent_id = rm_type(parent_fullname)
    is_link = is_link_name(parent_fullname)
    if is_link:
        parent_url = make_url(BASE_URL, parent_id)
    else:
        parent_url = make_url(get_url_from_fullname(base_link_id), parent_id)
    print('93', parent_url)
    data = requests.get(parent_url, headers=header).json()
    return gnpr_helper(get_replies(data, is_link))

# gets non-trivial data that is not in the author's history
def get_extra_data(url, is_comment_url):
    meta_data = get_meta_data(data, 1 if is_comment_url else 0)

    # starting from top

    # starting from bottom
    if is_comment_url:
        print('analyzing comment: ' + url)

    else:
        print('analyzing link: ' + url)


# MAIN AUTHOR LOOPER
# TODO later, deal with the 'after' section of an author
def author_looper(author):
    url = make_url(BASE_URL, 'user', author)
    data = requests.get(url, headers=header).json()
    posts = data['data']['children']

    key_list = ['time_since_last_comment', 'time_since_last_link',
                'time_since_last_link_or_comment', 'score',
                'upvote_ratio (links only)', 'is_reply_to_reply (comments only)',
                'response time', 'created_utc', 'author', 'id', 'subreddit',
                'body', 'urls_included', 'is_first_comment_by_author_in_thread',
                'url', 'kind' 'num_replies_before_this_reply']

    for p in posts:
        dictionary = {}
        for key in key_list:
            dictionary[key] = None

        main_data = p['data']
        score = main_data['score']

        # BOTH
        kind = p['kind']
        dictionary['kind'] = kind
        dictionary['score'] = score
        dictionary['created_utc'] = main_data['created_utc']
        dictionary['author'] = author
        dictionary['id'] = main_data['id']
        dictionary['subreddit'] = main_data['subreddit']

        if kind == 't1':
            # COMMENTS

            str_body = main_data['body'].encode('ascii', 'ignore')
            str_body = str.replace(str_body, '\n', ' ')
            str_body = str.replace(str_body, '\t', ' ')
            dictionary['body'] = str_body

            num_prior_replies = get_num_prior_replies(
                    main_data['link_id'],
                    main_data['parent_id'],
                    main_data['created_utc'])
            dictionary['num_replies_before_this_reply'] = num_prior_replies
        else:
            # LINKS
            dictionary['body'] = None

        print(dictionary)

author_looper('genkito')
