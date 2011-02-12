from django.core.exceptions import ValidationError

import test_utils

from feedback.validators import validate_no_urls, ExtendedURLValidator


class ValidatorTests(test_utils.TestCase):
    def test_chrome_url(self):
        """Make sure URL validator allows chrome and about URLs."""
        v = ExtendedURLValidator()

        # These will fail if validation error is raised.
        v('about:blank')
        v('chrome://mozapps/content/downloads/downloads.xul')

        # These should fail.
        self.assertRaises(ValidationError, v, 'about:')
        self.assertRaises(ValidationError, v, 'chrome:bogus')

    def test_url_in_text(self):
        """Find URLs in text."""
        patterns = (
            ('This contains no URLs.', False),
            ('I like the www. Do you?', False),
            ('If I write youtube.com, what happens?', False),
            ('Visit example.com/~myhomepage!', True),
            ('OMG http://foo.de', True),
            ('www.youtube.com is the best', True),
        )
        for pattern in patterns:
            if pattern[1]:
                self.assertRaises(ValidationError, validate_no_urls,
                                  pattern[0])
            else:
                validate_no_urls(pattern[0]) # Will fail if exception raised.
