#!/usr/bin/python2.6
import json
import sys

from amcat.db import dbtoolkit; db=dbtoolkit.amcatDB()
from amcat.model.article import Article, ArticleText, ArticlePost

PROPS = ['headline', 'byline', 'section', 'date', 'pagenr',
         'url', 'externalid', 'text', 'medium']

BATCH = int(sys.argv[1])

def parse(js):
    index = {}
    tree = {}

    for doc in js:
        index[doc['id']] = doc

        if doc['parent'] is not None:
            tree[doc['parent']].append(doc['id'])
        else:
            tree[doc['id']] = []

    return index, tree

def create_article(art):
    del art['id']
    del art['parent']

    args = dict(metastring={})
    for k,v in art.items():
        if k in PROPS:
            args[str(k)] = v
        else:
            args['metastring'][k] = v

    args['metastring'] = unicode(args['metastring'])
    args['length'] = len(args['text'])

    text = args['text']
    del args['text']

    id = Article.create(db, batch=BATCH, **args).id
    ArticleText.create(db, article=id, text=text, type=2, insertuserid=2, encoding=2)

    return id

def create_comment(pid, cid):
    ArticlePost.create(db, article=cid, parent=pid)

def main(path):
    js = json.load(open(path))
    print('JSON loaded')
    index, tree = parse(js)
    print('Articles parsed')

    for j, (parent, children) in enumerate(tree.items()):
        parent = index[parent]
        children = map(lambda i: index[i], children)

        pid = create_article(parent)
        for c in children:
            cid = create_article(c)
            create_comment(pid, cid)

        print(j+1, '/', len(tree))

        db.commit()

if __name__ == '__main__':
    main(sys.argv[2])