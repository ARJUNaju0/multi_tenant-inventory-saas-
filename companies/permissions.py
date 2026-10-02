from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CompanySerializer


class MyCompanyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        company = request.user.company
        serializer = CompanySerializer(company)

        return Response(serializer.data)

    def patch(self, request):
        company = request.user.company
        serializer = CompanySerializer(
            company,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)