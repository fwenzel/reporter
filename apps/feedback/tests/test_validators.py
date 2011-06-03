from django.core.exceptions import ValidationError

import test_utils

from feedback.validators import (validate_no_urls, validate_no_private_ips,
                                 ExtendedURLValidator)


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

    def test_private_ips_not_allowed(self):
        """Make sure private IPs can't be submitted as URLs."""
        patterns = (
            ('https://mozilla.com', False),
            ('http://tofumatt.com', False),
            ('youtube.com', False),
            ('0.0.0.0', True),
            ('http://127.0.0.1', True),
            ('HTTP://10.0.0.13', True),
            ('https://192.168.0.4', True),
        )
        for pattern in patterns:
            if pattern[1]:
                self.assertRaises(ValidationError, validate_no_private_ips,
                                  pattern[0])
            else:
                validate_no_private_ips(pattern[0])

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
