"""factory_boy fixtures for the User model."""
from __future__ import annotations

import factory

from apps.users.models import User

DEFAULT_TEST_PASSWORD = "Str0ngPass!23"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    full_name = factory.Faker("name")
    status = User.Status.ACTIVE

    @factory.post_generation
    def password(self, create: bool, extracted: str | None, **kwargs: object) -> None:
        password = extracted or DEFAULT_TEST_PASSWORD
        self.set_password(password)
        if create:
            self.save()
