import factory
from factory.django import DjangoModelFactory

from apps.accounts.models import User

class UserFactory(DjangoModelFactory):
  class Meta:
    model = User
    django_get_or_create = {"username",}

  username = factory.Sequence(lambda n: f"user{n}")
  email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
  role = User.Role.STUDENT

  @factory.post_generation
  def password(self, create, extracted, **kwargs):
    # Passing password=... as a kwarg to UserFactory() sets the raw
    # password via set_password() (properly hashed), rather than
    # being written as a literal model field.
    raw_password = extracted or "testpass123"
    self.set_password(raw_password)
    if create:
        self.save()