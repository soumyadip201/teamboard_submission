# TeamBoard Architecture Notes

## Request and data flow

```text
Company registration
       |
       v
Django User created
       |
       v
post_save signal
       |
       +----> Company row
       |
       +----> secrets.token_urlsafe(32)
       |
       v
JWT + API key returned

Protected KB query
       |
       v
JWTAuthentication
       |
       v
request.user.company
       |
       +----> Q(question__icontains=term)
       |       OR Q(answer__icontains=term)
       |
       +----> count + result evaluation
       |
       +----> QueryLog write
       |
       v
transaction.atomic() guarantees search/count/log succeed together

Admin summary
       |
       v
IsAdminUser
       |
       v
QueryLog aggregate + grouped counts
       |
       v
Platform usage response
```

## Design decisions

### 1. Signal for Company/API key creation

Registration creates only the Django `User` in the view. Company creation and credential generation are domain side effects owned by a `post_save` signal. This prevents a second code path from accidentally creating a Company without an API key.

### 2. JWT by default

DRF is configured globally with JWT authentication and `IsAuthenticated`. Public endpoints explicitly override that policy. This makes the secure behavior the default for any future endpoint.

### 3. Transactional query logging

KB search evaluation, result count, and QueryLog creation occur inside a single transaction. If the log write fails, the request does not leave partial usage state behind.

### 4. Database-side usage aggregation

The usage summary delegates counting and grouping to PostgreSQL through Django ORM aggregation rather than loading every QueryLog row into Python. This is the intended scalable pattern for platform-wide metrics.
