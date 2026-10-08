# Postman Runbook

1. Start PostgreSQL with `docker compose up -d db`.
2. Run migrations and seed: `python manage.py migrate` then `python manage.py seed_kb`.
3. Start Django: `python manage.py runserver`.
4. Import `postman_collection.json`.
5. Run requests 01-09 in sequence. Request 01 or 03 stores the access token in collection variables.
6. Promote `acmecorp` to admin with `python manage.py promote_admin --username acmecorp` or change `api_company.role` to `admin` in pgAdmin.
7. Run **Admin Login Helper** to save an admin access token.
8. Run 10 for the admin usage summary.
9. In pgAdmin, inspect `api_querylog` and take the required evidence screenshot for scenario 11.

## Failure scenarios to capture

- Duplicate username -> `400`
- Wrong password -> `401`
- KB query without JWT -> `401`
- Missing `search` -> `400`
- Client calling admin summary -> `403`

## Success scenarios to capture

- Registration -> `201` with API key/JWT
- KB query -> `200` with results
- KB query with no match -> `200` with count `0`
- Admin summary -> `200` with aggregates
