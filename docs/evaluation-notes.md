# TeamBoard Evaluation / Viva Notes

This file maps likely review questions to the implementation.

## 1. Why link Company to Django User with OneToOneField?
A user represents the authentication identity; Company represents the B2B customer profile and role/API credential. One user owns exactly one company profile.

## 2. Why generate the API key in a signal instead of the register view?
The brief explicitly requires automatic Company creation and API-key generation in a `post_save` signal. Keeping this side effect in the signal means any new User gets its Company profile consistently, not only users created through one view.

## 3. Why use `secrets.token_urlsafe(32)`?
It is the exact credential-generation mechanism requested by the assignment and is appropriate for generating an unpredictable API key. The value is stored in the Company row.

## 4. Why is role never accepted from the registration body?
A client must not be able to register itself as an admin. The model defaults to `client`, and admin promotion is an explicit server-side operation.

## 5. Why JWT if an API key is also issued?
The assignment requires SimpleJWT as the global DRF authentication mechanism. The API key is still provisioned as the company's B2B credential, while the specified protected endpoints are authorized using JWT.

## 6. Why use `request.user.company`?
The company must be derived from a credential the server validated. Taking a company ID from request JSON would allow one authenticated client to claim another company's identity.

## 7. Why use Q objects?
The search must match the same term in either `question` or `answer`. `Q` provides database-side OR logic: `Q(question__icontains=term) | Q(answer__icontains=term)`.

## 8. Why `icontains`?
The brief asks for case-insensitive substring matching. It means terms such as `JWT`, `jwt`, or a substring of an answer can match.

## 9. Why `transaction.atomic()` around search + log creation?
The usage log is part of the query operation's consistency boundary. If the log insert fails, the transaction rolls back rather than leaving a partial usage record.

## 10. Why log searches that return zero results?
Billing/usage is based on queries made, not answers found. A query that returns zero rows still consumes API/database resources and therefore still creates a QueryLog.

## 11. Why return 200 with an empty list instead of 404?
The endpoint queried the collection successfully; zero matches is a valid result, not a missing resource.

## 12. Why create a custom permission class?
The admin dashboard is controlled by the application's `Company.role`. The brief explicitly says not to use Django `is_staff` or `is_superuser`.

## 13. Why aggregate in the database?
`QueryLog.objects.aggregate()`, `values().distinct().count()`, and grouped `values().annotate()` let PostgreSQL perform counting and grouping. Pulling every query log into Python would use more memory and application CPU as usage grows.

## 14. Why seed data through a management command?
KB entries are platform-owned and are not exposed through a public create endpoint. A management command is repeatable, version-controlled, and appropriate for local/demo seeding.

## 15. What happens on duplicate registration?
The view detects an existing username and returns `400 Bad Request` without creating a second User/Company pair. An `IntegrityError` is also caught for race-condition safety.

## 16. What should be demonstrated in Postman?
Run the 11 required scenarios from `postman_collection.json`: registration success/failure, login success/failure, protected query success/failure cases, client/admin authorization, and QueryLog verification in PostgreSQL.
