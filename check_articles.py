from app import app, db
from models import Article

with app.app_context():
    articles = Article.query.order_by(Article.id).all()
    for a in articles:
        content_len = len(a.content_md) if a.content_md else 0
        summary_len = len(a.summary) if a.summary else 0
        print(f'{a.id}: {a.title}')
        print(f'   slug={a.slug} cat={a.category} author={a.author}')
        print(f'   content_md={content_len} chars summary={summary_len} chars pub={a.published}')
