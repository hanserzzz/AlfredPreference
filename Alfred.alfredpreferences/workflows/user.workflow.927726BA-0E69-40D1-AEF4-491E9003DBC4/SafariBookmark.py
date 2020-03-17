# -*- coding: utf-8 -*-
# @author = joslyn

import sys
import os
from workflow import Workflow
from biplist import *

bookmark_file_path = '~/Library/Safari/Bookmarks.plist'

bm_type = 'WebBookmarkType'
bm_type_folder = 'WebBookmarkTypeList'
bm_type_page = 'WebBookmarkTypeLeaf'
web_list = []
sub_list = []

SEARCH_TYPE_NORMAL = 0
SEARCH_TYPE_FOLDER = 1

wf = None

reload(sys)
sys.setdefaultencoding("utf8")


def filter_plist(bm_folder):
    if bm_folder[bm_type] in [bm_type_folder, bm_type_page]:
        if 'Title' in bm_folder.keys():
            if bm_folder['Title'] != 'BookmarksMenu':
                return True
            else:
                return False
        else:
            return True
    else:
        return False


def transform_title(parent):
    if parent == 'BookmarksBar':
        parent = u'Favorite'
    elif parent == 'com.apple.ReadingList':
        parent = u'ReadingList'
    return parent


def get_sub_list(children, parent, path):
    parent = transform_title(parent);
    join_char = '' if parent == '/' else '/'
    for i, child in enumerate(children):
        sub_parent = child['Title'] if 'Title' in child.keys() else ''
        sub_parent = transform_title(sub_parent);
        parent_path = join_char.join([path, sub_parent]) if sub_parent else path
        if child[bm_type] == bm_type_folder:
            sub_list.append(get_sub_from_dict(child, parent, parent_path))
            if 'Children' in child.keys():
                get_sub_list(child['Children'], sub_parent, parent_path)
            else:
                pass
        else:
            sub_from_def = get_sub_from_def(child, parent, parent_path)
            sub_list.append(sub_from_def)
            web_list.append(sub_from_def)
    return list(set(web_list)), sub_list


def get_main_children():
    temp_list = []
    try:
        plist = readPlist(os.path.expanduser(bookmark_file_path))
        temp_list = list(filter(filter_plist, plist['Children']))

    except (InvalidPlistException, NotBinaryPlistException) as e:
        print("Not a plist:", e)
    return temp_list


def get_sub_from_def(child, parent, path):
    return child[bm_type], child['URIDictionary']['title'], child['URLString'],\
           child['URLString'], 'image/web.png', True, parent, path


def get_sub_from_dict(child, parent, path):
    if child['Title'] == 'BookmarksBar':
        return child[bm_type], u'Favorite',  u'个人收藏', None, 'image/folder.png', False, parent, path
    elif child['Title'] == 'com.apple.ReadingList':
        return child[bm_type], u'ReadingList', u'阅读列表', None, 'image/folder.png', False, parent, path
    else:
        return child[bm_type], child['Title'], None, None, 'image/folder.png', False, parent, path


def list_data():
    main_children = get_main_children()
    return get_sub_list(main_children, '/', '/')


def main(wf):
    wf.logger.debug('------->')
    all_web_list, all_sub_list = wf.cached_data(name='list_data', data_func=list_data, max_age=5)
    one_level_dir = list(filter(lambda x: x[6] == '/', all_sub_list))

    if len(wf.args):
        query = wf.args[0].lstrip()
        search_type = SEARCH_TYPE_FOLDER if query[:1] == '/' else SEARCH_TYPE_NORMAL
    else:
        search_type = SEARCH_TYPE_NORMAL
        query = None

    if query:
        if search_type == SEARCH_TYPE_NORMAL:
            main_plist = wf.filter(query, all_web_list, key=lambda x: x[1], max_results=12)
        else:
            query_folder = query.split('/')
            if len(query_folder) > 2:
                main_plist = filter(lambda x: x[6] == query_folder[:-1][-1], all_sub_list)
            else:
                main_plist = one_level_dir
            main_plist = wf.filter(query_folder[-1], main_plist, key=lambda x: x[1], max_results=12)
    else:
        main_plist = one_level_dir

    for item_type, title, subtitle, target, icon, valid, parent, path in main_plist:
        autocomplete_folder = u'{0}/{1}/'.format(query[:str(query).rfind(u'/')], title)
        autocomplete = autocomplete_folder if item_type == bm_type_folder else None
        large_text = title if item_type == bm_type_folder else subtitle
        wf.add_item(title=title, subtitle=subtitle, arg=target, icon=icon, valid=valid,
                    autocomplete=autocomplete, copytext=subtitle, quicklookurl=subtitle, largetext=path)

    wf.send_feedback()


if __name__ == '__main__':
    update_settings = {'github_slug': u'JoslynWu/Alfred-SafariBookmark'}
    wf = Workflow(update_settings=update_settings)
    sys.exit(wf.run(main))
