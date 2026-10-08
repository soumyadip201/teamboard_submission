from django.core.management.base import BaseCommand

from api.models import KBEntry


SEED_ENTRIES = [
    {
        "question": "What is select_related in Django ORM?",
        "answer": "select_related performs a SQL JOIN and fetches the related object in the same database query, making it useful for foreign key and one-to-one relationships.",
        "category": "database",
    },
    {
        "question": "What is prefetch_related in Django ORM?",
        "answer": "prefetch_related performs a separate query and joins the related objects in Python, which is useful for many-to-many and reverse relationships.",
        "category": "database",
    },
    {
        "question": "How does transaction.atomic work in Django?",
        "answer": "transaction.atomic wraps a block in a database transaction so all writes commit together or roll back together if an exception occurs.",
        "category": "database",
    },
    {
        "question": "What is a JWT token?",
        "answer": "A JSON Web Token is a signed token containing claims that a server can verify without keeping session state for every request.",
        "category": "api",
    },
    {
        "question": "How does JWT authentication work in DRF?",
        "answer": "The client sends a Bearer access token, DRF authentication verifies the token signature and expiry, then exposes the authenticated user as request.user.",
        "category": "api",
    },
    {
        "question": "What are Q objects in Django?",
        "answer": "Q objects allow complex database filters using boolean logic such as OR and AND, including expressions like Q(question__icontains=term) | Q(answer__icontains=term).",
        "category": "database",
    },
    {
        "question": "What are Django signals?",
        "answer": "Signals let code react to model lifecycle events such as post_save without putting secondary side effects directly into the view.",
        "category": "framework",
    },
    {
        "question": "What is an API gateway?",
        "answer": "An API gateway is an entry point that can route requests, apply authentication, rate limits, observability, and other cross-cutting concerns before forwarding traffic to backend services.",
        "category": "api",
    },
    {
        "question": "What is database indexing?",
        "answer": "A database index is an auxiliary data structure that can speed up lookups and ordering at the cost of additional storage and write overhead.",
        "category": "database",
    },
    {
        "question": "What is Docker used for?",
        "answer": "Docker packages applications and their dependencies into reproducible containers. It is commonly used to run infrastructure such as PostgreSQL consistently across environments.",
        "category": "cloud",
    },
    {
        "question": "What is dependency injection in Django?",
        "answer": "Dependency injection means supplying a component with the dependencies it needs rather than constructing those dependencies internally, improving testability and separation of concerns.",
        "category": "framework",
    },
    {
        "question": "What is REST?",
        "answer": "REST is a style for designing networked APIs around resources, standard HTTP methods, stateless requests, and representations of resource state.",
        "category": "api",
    },
    {
        "question": "What is PostgreSQL?",
        "answer": "PostgreSQL is an open-source relational database known for strong SQL support, transactions, indexes, constraints, and extensibility.",
        "category": "database",
    },
    {
        "question": "What is a database transaction?",
        "answer": "A transaction groups operations into one logical unit of work that should satisfy atomicity, consistency, isolation, and durability guarantees.",
        "category": "general",
    },
    {
        "question": "Why use environment variables for database credentials?",
        "answer": "Environment variables keep secrets and environment-specific configuration out of source code and version control, reducing accidental credential exposure.",
        "category": "cloud",
    },
]


class Command(BaseCommand):
    help = "Seed TeamBoard with knowledge-base entries. Safe to run multiple times."

    def handle(self, *args, **options):
        created = 0
        updated = 0

        for entry in SEED_ENTRIES:
            _, was_created = KBEntry.objects.update_or_create(
                question=entry["question"],
                defaults={
                    "answer": entry["answer"],
                    "category": entry["category"],
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"KB seed complete: {created} created, {updated} updated, "
                f"{KBEntry.objects.count()} total entries."
            )
        )
