"""
Test suite for all utils in the `core` application
"""
from django.test import override_settings

from cms.api import Page
from cms.test_utils.testcases import CMSTestCase

from richie.apps.core.factories import PageFactory
from richie.apps.core.helpers import create_i18n_page


class PagesTests(CMSTestCase):
    """Integration tests that actually render pages"""

    def test_pages_i18n_menu(self):
        """
        Create an i18n page and check its rendering on the site
        """
        content = {"fr": "Tableau de bord", "en": "Dashboard"}
        create_i18n_page(
            content,
            is_homepage=True,
            published=True,
            template="richie/single_column.html",
        )
        # Get the root page in french...
        root = Page.objects.get_home()
        response = self.client.get(root.get_absolute_url("fr"))
        self.assertEqual(200, response.status_code)
        # ... and make sure the page menu is present in french on the page
        self.assertIn(content["fr"], response.rendered_content)

        # Get the root page in english...
        response = self.client.get(root.get_absolute_url("en"))
        self.assertEqual(200, response.status_code)
        # ... and make sure the page menu is present in english on the page
        self.assertIn(content["en"], response.rendered_content)

    @override_settings(
        LANGUAGES=(("fr-ca", "Canadian"), ("es", "Spanish")),
        LANGUAGE_CODE="fr-ca",
        CMS_LANGUAGES={},
    )
    def test_pages_i18n_hreflang(self):
        """
        The hreflang links should be configured to avoid duplicate content accross languages.
        """
        content = {"fr-ca": "Un, deux", "es": "uno, dos"}
        create_i18n_page(
            content,
            published=True,
            template="richie/single_column.html",
        )
        page = Page.objects.get(publisher_is_draft=False)

        # ... and make sure the hreflinks are on the page in all languages
        for language in ["fr-ca", "es"]:
            response = self.client.get(page.get_absolute_url(language))
            self.assertEqual(200, response.status_code)
            self.assertIn(
                '<link rel="alternate" href="/fr-ca/un-deux/" hreflang="fr-ca" />',
                response.rendered_content,
            )
            self.assertIn(
                '<link rel="alternate" href="/es/uno-dos/" hreflang="es" />',
                response.rendered_content,
            )

    @override_settings(SENTRY_DSN="https://example.com/sentry/dsn")
    @override_settings(RELEASE="9.8.7")
    @override_settings(ENVIRONMENT="test_pages")
    def test_page_includes_frontend_context(self):
        """
        Create a page and make sure it includes the frontend context as included
        in `base.html`.

        ⚠️ If this test fails, before fixing it, identify if this change has had
        ⚠️ an impact on frontend and update frontend accordingly.
        """
        page = PageFactory(should_publish=True, template="richie/single_column.html")
        response = self.client.get(page.get_public_url())
        self.assertContains(response, '"environment": "test_pages"')
        self.assertContains(response, '"release": "9.8.7"')
        self.assertContains(response, '"sentry_dsn": "https://example.com/sentry/dsn"')
