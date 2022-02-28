from typing import NewType 

sitename = NewType("site_name", str)
url = NewType("url", str)
article_text = NewType("article_text", str)
news_item = NewType("news_item", tuple[sitename, url, article_text])
'''tuple[site_name, url, acrticle_text]'''
