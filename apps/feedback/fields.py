from django.db.models.fields import URLField, CharField
from django.core.validators import URLValidator

from .validators import ExtendedURLValidator


class ExtendedURLField(URLField):
    """(Model) URLField that allows about: and chrome: URLs."""

    def __init__(self, *args, **kwargs):
        super(ExtendedURLField, self).__init__(*args, **kwargs)

        # Remove old URL validator, add ours instead.
        self.validators = filter(lambda x: not isinstance(x, URLValidator),
                                 self.validators)
        self.validators.append(ExtendedURLValidator(verify_exists=verify_exists))
