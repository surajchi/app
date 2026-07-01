import factory

from apps.markets.models import Exchange, Instrument


class ExchangeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Exchange

    code = factory.Sequence(lambda n: f"EXCH{n}")
    name = "Test Exchange"
    currency = "USD"


class InstrumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Instrument

    asset_class = "stock"
    symbol = factory.Sequence(lambda n: f"SYM{n}")
    name = "Test Instrument"
    currency = "USD"
