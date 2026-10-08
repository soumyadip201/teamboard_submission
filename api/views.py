from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Company, KBEntry, QueryLog
from .permissions import IsAdminUser
from .serializers import KBQuerySerializer, LoginSerializer, RegisterSerializer


def access_token_for(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": self._first_error(serializer)}, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data["username"]
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        company_name = serializer.validated_data["company_name"].strip()

        if not company_name:
            return Response({"error": "company_name cannot be blank"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                )
                company = user.company
                company.company_name = company_name
                company.save(update_fields=["company_name"])
        except IntegrityError:
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "username": user.username,
                "company_name": company.company_name,
                "api_key": company.api_key,
                "access": access_token_for(user),
            },
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    def _first_error(serializer):
        for field, messages in serializer.errors.items():
            if messages:
                return f"{field}: {messages[0]}"
        return "Invalid request body"


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": self._first_error(serializer)}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(
            request=request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"error": "Invalid username or password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            company = user.company
        except Company.DoesNotExist:
            return Response(
                {"error": "Company profile not found"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "access": access_token_for(user),
                "company_name": company.company_name,
                "api_key": company.api_key,
            },
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _first_error(serializer):
        for field, messages in serializer.errors.items():
            if messages:
                return f"{field}: {messages[0]}"
        return "Invalid request body"


class KBQueryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = KBQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"error": "search is required"}, status=status.HTTP_400_BAD_REQUEST)

        search_term = serializer.validated_data["search"]
        company = request.user.company

        with transaction.atomic():
            queryset = KBEntry.objects.filter(
                Q(question__icontains=search_term) |
                Q(answer__icontains=search_term)
            ).order_by("id")

            results_count = queryset.count()
            results = list(
                queryset.values("id", "question", "answer", "category")
            )
            QueryLog.objects.create(
                company=company,
                search_term=search_term,
                results_count=results_count,
            )

        return Response(
            {
                "search": search_term,
                "count": results_count,
                "results": results,
            },
            status=status.HTTP_200_OK,
        )


class UsageSummaryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_queries = QueryLog.objects.aggregate(total=Count("id"))["total"] or 0
        active_companies = QueryLog.objects.values("company").distinct().count()
        top_search_terms = list(
            QueryLog.objects
            .values("search_term")
            .annotate(count=Count("id"))
            .order_by("-count", "search_term")[:5]
        )

        return Response(
            {
                "total_queries": total_queries,
                "active_companies": active_companies,
                "top_search_terms": top_search_terms,
            },
            status=status.HTTP_200_OK,
        )
