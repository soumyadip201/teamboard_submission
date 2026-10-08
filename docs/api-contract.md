# TeamBoard API Contract

Base URL: `http://127.0.0.1:8000/api`

## 1. Register

`POST /auth/register/`

Public. Request:

```json
{
  "username": "acmecorp",
  "password": "securepass123",
  "company_name": "Acme Corp",
  "email": "dev@acmecorp.com"
}
```

`201 Created` returns `username`, `company_name`, `api_key`, `access`, and `role`.

## 2. Login

`POST /auth/login/`

Public. Request:

```json
{
  "username": "acmecorp",
  "password": "securepass123"
}
```

`200 OK` returns `access`, `company_name`, and `api_key`.

## 3. Knowledge Base Query

`POST /kb/query/`

JWT required.

Header:

```text
Authorization: Bearer <JWT access token>
```

Request:

```json
{"search": "select_related"}
```

`200 OK` returns:

```json
{
  "search": "select_related",
  "count": 1,
  "results": [
    {
      "id": 1,
      "question": "...",
      "answer": "...",
      "category": "database"
    }
  ]
}
```

## 4. Admin Usage Summary

`GET /admin/usage-summary/`

JWT required + `Company.role == admin`.

`200 OK` returns:

```json
{
  "total_queries": 284,
  "active_companies": 7,
  "top_search_terms": [
    {"search_term": "select_related", "count": 42}
  ]
}
```
