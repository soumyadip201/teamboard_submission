# TeamBoard - B2B Knowledge Base API

TeamBoard is a backend API for a B2B knowledge-base platform. Companies register, receive a unique API key, authenticate with JWT, query a curated Q&A knowledge base, and have every query recorded for platform-wide usage analytics.

This implementation follows the supplied Airtribe project brief: four API endpoints, PostgreSQL via Docker, Django signals for Company/API-key creation, JWT authentication by default, Q-object search across `question` and `answer`, transactional query logging, a custom admin permission, and ORM-based usage aggregation.

## What is implemented

| Requirement | Implementation |
|---|---|
| Company profile | `api/models.py` - `Company` with `OneToOneField(User)` |
| Automatic Company creation | `api/signals.py` + `ApiConfig.ready()` |
| API key | `secrets.token_urlsafe(32)` in the `post_save` signal |
| Knowledge base | `KBEntry` model + idempotent `seed_kb` management command |
| Usage tracking | `QueryLog` model |
| JWT | SimpleJWT as the global DRF authentication class |
| Public registration/login | `authentication_classes = []`, `AllowAny` |
| KB search | `Q(question__icontains=...) | Q(answer__icontains=...)` |
| Atomic query logging | `transaction.atomic()` around search/count/log write |
| Admin authorization | `IsAdminUser` checks `request.user.company.role` |
| Admin aggregation | `aggregate`, `distinct().count()`, `values().annotate()` |
| PostgreSQL | Docker Compose `postgres:17-alpine` |
| API documentation | `docs/api-contract.md` + Postman collection |
| Automated tests | `api/tests.py` (14 business-focused tests) |
| CI | `.github/workflows/ci.yml` |

## Architecture

```text
                    +----------------------+
                    |      API Client      |
                    +----------+-----------+
                               |
                         JWT Bearer Token
                               |
                               v
                    +----------------------+
                    | Django + DRF API     |
                    +----------+-----------+
                               |
              +----------------+----------------+
              |                |                |
              v                v                v
        User / Company       KBEntry          QueryLog
              |                                  ^
              |                                  |
              +-------- JWT / Role ---------------+
                               |
                               v
                     Admin Usage Summary

PostgreSQL runs as a Docker container and is the only persistence layer.
```

### Authentication choice

The platform issues two credentials during registration:

- **API key** - generated server-side by the Company `post_save` signal and returned to the customer.
- **JWT access token** - the required authorization mechanism for the protected endpoints in this assignment.

The brief explicitly requires SimpleJWT globally and says `/api/kb/query/` and `/api/admin/usage-summary/` are protected. The assignment does not require a custom `X-API-Key` authentication class, so the API key is provisioned and returned as specified without inventing an additional authentication protocol.

## Requirements

- Python 3.12+
- Docker Desktop with Docker Compose
- Git
- Postman
- Optional: pgAdmin for database inspection

The requirements file is pinned to specific versions. The current pinned stack uses Django 5.2.18, Django REST Framework 3.18.3, SimpleJWT 5.5.1, python-dotenv 1.2.4 and psycopg 3.3.6.

## 1. Setup

Clone the repository or extract the project.

```bash
git clone <your-repository-url>
cd teamboard_submission
```

Create the environment file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Change at least `SECRET_KEY` in `.env` to a long random value.

Create a virtual environment:

```bash
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 2. Start PostgreSQL

```bash
docker compose up -d db
```

Check it:

```bash
docker compose ps
```

The database is exposed on `localhost:5432` by default.

## 3. Apply migrations

```bash
python manage.py makemigrations --check
python manage.py migrate
```

`api/migrations/0001_initial.py` is already included, so `migrate` should create the required tables without needing to generate a new migration.

## 4. Seed the knowledge base

The platform pre-populates the KB. Run:

```bash
python manage.py seed_kb
```

This creates 15 useful technical Q&A entries across API, database, cloud, framework, and general categories. The command is idempotent and can safely be run again.

Verify:

```bash
python manage.py shell -c "from api.models import KBEntry; print(KBEntry.objects.count())"
```

Expected result: `15` or more if you add additional entries.

## 5. Run the server

```bash
python manage.py runserver
```

API base URL:

```text
http://127.0.0.1:8000/api/
```

## 6. Promote a user to admin

The assignment asks for admin access to be based on `Company.role`, not Django `is_staff` or `is_superuser`.

After registering a company, either update its Company row in pgAdmin so `role = admin`, or use the included helper:

```bash
python manage.py promote_admin --username acmecorp
```

Then log in again so you have a fresh JWT for the admin user.

## API endpoints

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/register/` | Public | Register a company, auto-create Company/API key, return JWT |
| POST | `/api/auth/login/` | Public | Validate credentials and return JWT + company credentials |
| POST | `/api/kb/query/` | JWT | Case-insensitive KB search and atomic QueryLog creation |
| GET | `/api/admin/usage-summary/` | JWT + ADMIN role | Platform usage statistics |

## Registration

Request:

```json
{
  "username": "acmecorp",
  "password": "securepass123",
  "company_name": "Acme Corp",
  "email": "dev@acmecorp.com"
}
```

Successful response: `201 Created`

```json
{
  "username": "acmecorp",
  "company_name": "Acme Corp",
  "api_key": "auto-generated-api-key",
  "access": "eyJ...",
  "role": "client"
}
```

The view never accepts or assigns `role` or `api_key`. The `Company` profile and API key are created in the `post_save` signal, as required.

Duplicate username: `400 Bad Request`

```json
{
  "error": "Username already exists"
}
```

## Login

Request:

```json
{
  "username": "acmecorp",
  "password": "securepass123"
}
```

Successful response: `200 OK`

```json
{
  "access": "eyJ...",
  "company_name": "Acme Corp",
  "api_key": "gT8x..."
}
```

Invalid credentials: `401 Unauthorized`

```json
{
  "error": "Invalid username or password"
}
```

The implementation uses Django's `authenticate()` exactly as required.

## Knowledge-base query

Endpoint:

```text
POST /api/kb/query/
```

Header:

```text
Authorization: Bearer <access-token>
Content-Type: application/json
```

Request:

```json
{
  "search": "select_related"
}
```

The view gets the company from `request.user.company`, never from request data.

The search uses:

```python
Q(question__icontains=search_term) | Q(answer__icontains=search_term)
```

The search, result count, and QueryLog insert execute in one `transaction.atomic()` block. A query that returns zero results is still logged because the platform is tracking usage, not just successful searches.

Successful response: `200 OK`

```json
{
  "search": "select_related",
  "count": 1,
  "results": [
    {
      "id": 1,
      "question": "What is select_related in Django ORM?",
      "answer": "select_related performs a SQL JOIN...",
      "category": "database"
    }
  ]
}
```

Missing or blank `search`: `400 Bad Request`.

No token: `401 Unauthorized`.

No matching entries: `200 OK` with:

```json
{
  "search": "nothing-here",
  "count": 0,
  "results": []
}
```

A `QueryLog` row is still created for that request.

## Admin usage summary

Endpoint:

```text
GET /api/admin/usage-summary/
```

A normal client token receives `403 Forbidden`.

Admin authorization is implemented in `api/permissions.py`:

```python
request.user.company.role == Company.Role.ADMIN
```

It does not use `is_staff` or `is_superuser`.

The endpoint returns:

```json
{
  "total_queries": 284,
  "active_companies": 7,
  "top_search_terms": [
    {"search_term": "select_related", "count": 42},
    {"search_term": "transaction atomic", "count": 31},
    {"search_term": "jwt authentication", "count": 28},
    {"search_term": "q objects", "count": 19},
    {"search_term": "signals django", "count": 14}
  ]
}
```

The exact numbers depend on the queries made against your local database. The implementation uses Django ORM aggregation and grouping, not Python-side counting.

## pgAdmin verification

Connect pgAdmin to the Docker PostgreSQL instance with:

```text
Host:     localhost
Port:     5432
Database: teamboard
Username: teamboard
Password: <DB_PASSWORD from .env>
```

After running migrations you should see these application tables:

- `api_company`
- `api_kbentry`
- `api_querylog`

You should also see Django's built-in auth/session tables.

After a successful KB query, inspect `api_querylog` and confirm:

- company points to the authenticated company
- `search_term` matches the request
- `results_count` matches the API response
- `queried_at` is populated

## Postman collection

Import:

```text
postman_collection.json
```

The collection covers the required 11 scenarios, plus one clearly marked Admin Login Helper request needed to obtain a fresh admin JWT after changing the role:

| # | Scenario | Expected |
|---|---|---|
| 1 | Register a new company | `201` + API key + JWT |
| 2 | Register with duplicate username | `400` |
| 3 | Login with valid credentials | `200` + JWT |
| 4 | Login with wrong password | `401` |
| 5 | Query KB without token | `401` |
| 6 | Query KB with valid token, keyword with results | `200` + results |
| 7 | Query KB with valid token, no matching results | `200` + count `0` |
| 8 | Query KB with missing search field | `400` |
| 9 | Usage summary with CLIENT token | `403` |
| 10 | Usage summary with ADMIN token | `200` + stats |
| 11 | Verify QueryLog in PostgreSQL/pgAdmin | Row exists |

### Suggested Postman order

1. Run **01 - Register new company**.
2. Run **03 - Login valid credentials**.
3. Run **06 - Query KB with results**.
4. Run **07 - Query KB with no matching results**.
5. Run **08 - Query KB missing search**.
6. Run **05 - Query KB without token**.
7. Run **09 - Usage summary with CLIENT token**.
8. Promote the same company to admin using pgAdmin or `promote_admin`.
9. Run the **Admin Login Helper** request in the collection.
10. Run **10 - Usage summary with ADMIN token**.
11. Refresh pgAdmin and verify `api_querylog` for scenario 11.

## Automated tests

Run:

```bash
python manage.py test
```

The suite covers the real business logic, including:

- signal-created Company + API key
- registration and duplicate handling
- JWT login
- invalid login
- JWT-protected KB query
- case-insensitive Q-object search
- QueryLog creation
- zero-result logging
- missing search validation
- company-scoped QueryLog ownership
- transaction rollback when the log write fails
- client `403` for the admin endpoint
- admin aggregation and top search terms

## CI

A GitHub Actions workflow is included at `.github/workflows/ci.yml`. It starts PostgreSQL, installs pinned dependencies, runs `makemigrations --check`, Django system checks, migrations, and the complete test suite.

## Project structure

```text
teamboard_submission/
├── .github/workflows/ci.yml
├── api/
│   ├── admin.py
│   ├── apps.py
│   ├── management/commands/
│   │   ├── promote_admin.py
│   │   └── seed_kb.py
│   ├── migrations/0001_initial.py
│   ├── models.py
│   ├── permissions.py
│   ├── serializers.py
│   ├── signals.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── docs/
│   ├── api-contract.md
│   ├── architecture.md
│   └── screenshots/README.md
├── teamboard/
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── .dockerignore
├── .env.example
├── .gitignore
├── docker-compose.yml
├── manage.py
├── postman_collection.json
├── README.md
└── requirements.txt
```

## Submission checklist

Before submitting your GitHub link, verify:

- [ ] Repository is public.
- [ ] `README.md` is present and complete.
- [ ] `requirements.txt` contains pinned versions.
- [ ] `.env` is not committed.
- [ ] PostgreSQL starts with `docker compose up -d db`.
- [ ] `python manage.py migrate` succeeds.
- [ ] `python manage.py seed_kb` creates at least 10 KB entries.
- [ ] `python manage.py test` passes.
- [ ] All 11 Postman scenarios are tested.
- [ ] Postman collection JSON is committed.
- [ ] `docs/screenshots/` contains your actual success/failure/pgAdmin evidence screenshots.
- [ ] The final GitHub URL is the URL submitted to Airtribe.

## Notes

Do not commit `.env` or real database credentials. Use `.env.example` as the template.

The screenshots directory contains a capture guide rather than fabricated evidence. Take the required screenshots from your own running application and place them in that directory before submission.
