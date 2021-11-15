from typing import NewType

sitename = NewType("sitename", str)
url = NewType("url", str)
article_text = NewType("article_text", str)
news_item = NewType("news_item", tuple[sitename, url, article_text])
