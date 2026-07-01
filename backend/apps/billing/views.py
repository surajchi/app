"""Billing API: plans, subscription lifecycle, invoices, payment methods, webhook.

Admin endpoints reuse the RBAC permission catalog (subscriptions.manage,
payments.refund).
"""

from __future__ import annotations

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing import services
from apps.billing.models import Invoice, PaymentMethod, Plan, Subscription
from apps.billing.serializers import (
    AddPaymentMethodSerializer,
    CancelSerializer,
    InvoiceSerializer,
    PaymentMethodSerializer,
    PlanSerializer,
    SubscribeSerializer,
    SubscriptionSerializer,
)
from apps.rbac.permissions import HasPermission
from integrations.payments.registry import get_payment_provider


@extend_schema(tags=["billing"])
class PlanListView(generics.ListAPIView):
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]
    authentication_classes: list = []
    queryset = Plan.objects.filter(is_active=True)


@extend_schema(tags=["billing"])
class SubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        sub = services.current_subscription(request.user)
        return Response(
            {
                "subscription": SubscriptionSerializer(sub).data if sub else None,
                "entitlements": services.entitlements(request.user),
            }
        )


@extend_schema(tags=["billing"], request=SubscribeSerializer)
class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = SubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plan = Plan.objects.get(code=serializer.validated_data["plan"], is_active=True)
        try:
            sub = services.subscribe(
                user=request.user,
                plan=plan,
                start_trial=serializer.validated_data["start_trial"],
            )
        except services.PaymentError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_402_PAYMENT_REQUIRED)
        return Response(SubscriptionSerializer(sub).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["billing"], request=CancelSerializer)
class CancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = CancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            sub = services.cancel(
                user=request.user,
                at_period_end=serializer.validated_data["at_period_end"],
            )
        except services.PaymentError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(SubscriptionSerializer(sub).data)


@extend_schema(tags=["billing"])
class InvoiceListView(generics.ListAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[Invoice]:
        return Invoice.objects.filter(user=self.request.user)


@extend_schema(tags=["billing"])
class PaymentMethodListCreateView(generics.ListCreateAPIView):
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet[PaymentMethod]:
        return PaymentMethod.objects.filter(user=self.request.user)

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = AddPaymentMethodSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        provider = get_payment_provider()
        make_default = data["make_default"]
        if make_default:
            PaymentMethod.objects.filter(user=request.user, is_default=True).update(
                is_default=False
            )
        method = PaymentMethod.objects.create(
            user=request.user,
            provider=provider.name,
            provider_payment_method_id=f"{provider.name}_pm_{data['last4']}",
            brand=data["brand"],
            last4=data["last4"],
            exp_month=data["exp_month"],
            exp_year=data["exp_year"],
            is_default=make_default,
        )
        return Response(PaymentMethodSerializer(method).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["billing"])
class PaymentMethodDefaultView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request, pk: str) -> Response:
        method = get_object_or_404(PaymentMethod, pk=pk, user=request.user)
        PaymentMethod.objects.filter(user=request.user, is_default=True).update(is_default=False)
        method.is_default = True
        method.save(update_fields=["is_default", "updated_at"])
        return Response(PaymentMethodSerializer(method).data)


@extend_schema(tags=["billing"])
class WebhookView(APIView):
    permission_classes = [AllowAny]
    authentication_classes: list = []

    def post(self, request: Request) -> Response:
        provider = get_payment_provider()
        signature = request.headers.get("X-Webhook-Signature")
        if not provider.verify_webhook(request.body, signature):
            return Response({"detail": "Invalid signature."}, status=status.HTTP_400_BAD_REQUEST)
        handled = services.handle_webhook_event(
            request.data if isinstance(request.data, dict) else {}
        )
        return Response({"handled": handled})


# --- Admin (RBAC-gated) -----------------------------------------------------


@extend_schema(tags=["billing"])
class AdminSubscriptionListView(generics.ListAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "subscriptions.manage"

    def get_queryset(self) -> QuerySet[Subscription]:
        qs = Subscription.objects.select_related("plan", "user").all()
        if (sub_status := self.request.query_params.get("status")) is not None:
            qs = qs.filter(status=sub_status)
        return qs


@extend_schema(tags=["billing"])
class RefundView(APIView):
    permission_classes = [IsAuthenticated, HasPermission]
    required_permission = "payments.refund"

    def post(self, request: Request, pk: str) -> Response:
        invoice = get_object_or_404(Invoice, pk=pk)
        if invoice.status != "paid":
            return Response(
                {"detail": "Only paid invoices can be refunded."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        services.refund_invoice(invoice=invoice)
        return Response(InvoiceSerializer(invoice).data)
