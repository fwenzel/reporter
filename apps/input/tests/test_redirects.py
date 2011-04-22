from input.tests import InputTestCase, enforce_ua


class RedirectTests(InputTestCase):
    @enforce_ua
    def test_redirects(self):
        redirect = lambda x: '/en-US/%s' % x
        redirs = {
                '/feedback': '/en-US/feedback',
                '/thanks': '/en-US/thanks',
                '/themes': '/en-US/themes',
                '/sites': redirect('sites'),
                '/en-US/release/themes': redirect('themes'),
                '/en-US/beta/sites': redirect('sites'),
                }
        for link, redir in redirs.iteritems():
            self.assertRedirects(self.fxclient.get(link, follow=True), redir,
                                 301)

    def test_search(self):
        r = self.fxclient.get('/search', follow=True)
        assert r.status_code != 404
