# Contributing to TeamBoard

This repository is an assignment submission, but the code follows a small production-style structure.

Before opening a pull request:

```bash
python manage.py makemigrations --check --dry-run
python manage.py check
python manage.py test
```

Do not commit `.env`, real database credentials, access tokens, or API keys.
