# -*- coding: utf-8 -*-
from django.db import models
from django.core.urlresolvers import NoReverseMatch, reverse
from django.utils.translation import ugettext_lazy as _


class HaystackResults(models.Model):
    """ Our fake model, used for mounting :py:class:`~haystackbrowser.admin.HaystackResultsAdmin`
    onto the appropriate AdminSite.

    .. note::

        the model is marked as unmanaged, so will never get created via ``syncdb``.
    """
    def validate:
        pass
    
    class Meta:
        managed = False
        verbose_name = _('Search result')
        verbose_name_plural = _('Search results')


class SearchResultWrapper(object):
    """Value object which consumes a standard Haystack SearchResult, and the current
    admin site, and exposes additional methods and attributes for displaying the data
    appropriately.

    :param obj: the item to be wrapped.
    :type obj: object
    :param admin_site: the parent site instance.
    :type admin_site: AdminSite object

    """
    def __init__(self, obj, admin_site=None):
        self.admin = admin_site
        self.object = obj

    def get_app_url(self):
        """Resolves a given object's app into a link to the app administration.

        .. warning::
            This link may return a 404, as pretty much anything may
            be reversed and fit into the ``app_list`` urlconf.

        :return: string or None
        """
        try:
            return reverse('%s:app_list' % self.admin, kwargs={
                'app_label': self.object.app_label,
            })
        except NoReverseMatch:
            return None

    def get_model_url(self):
        """Generates a link to the changelist for a specific Model in the administration.

        :return: string or None
        """
        try:
            parts = (self.admin, self.object.app_label, self.object.model_name)
            return reverse('%s:%s_%s_changelist' % parts)
        except NoReverseMatch:
            return None

    def get_pk_url(self):
        """Generates a link to the edit page for a specific object in the administration.

        :return: string or None
        """
        try:
            parts = (self.admin, self.object.app_label, self.object.model_name)
            return reverse('%s:%s_%s_change' % parts, args=(self.object.pk,))
        except NoReverseMatch:
            return None

    def get_additional_fields(self):
        """Find all fields in the Haystack SearchResult which have not already
        appeared in the stored fields.

        :return: dictionary of field names and values.
        """
        additional_fields = {}
        stored_fields = self.get_stored_fields().keys()
        for key, value in self.object.get_additional_fields().items():
            if key not in stored_fields:
                additional_fields[key] = value
        return additional_fields

    def get_content_field(self):
        """Find the name of the main content field in the Haystack SearchIndex
        for this object.

        :return: string representing the attribute name.
        """
        return self.object.searchindex.get_content_field()

    def get_content(self):
        """Given the name of the main content field in the Haystack Search Index
         for this object, get the named attribute on this object.

         :return: whatever is in ``self.object.<content_field_name>``
        """
        return getattr(self.object, self.get_content_field())

    def get_stored_field_count(self):
        """
        Provides mechanism for finding the number of stored fields stored on
        this Search Result.

        :return: the count of all stored fields.
        :rtype: integer
        """
        return len(self.object.get_stored_fields().keys())

    def get_additional_field_count(self):
        """
        Provides mechanism for finding the number of stored fields stored on
        this Search Result.

        :return: the count of all stored fields.
        :rtype: integer
        """
        return len(self.get_additional_fields().keys())

    def __getattr__(self, attr):
        return getattr(self.object, attr)


class FacetWrapper(object):
    """
    A simple wrapper around `sqs.facet_counts()` to filter out things with
    0, and re-arrange the data in such a way that the template can handle it.
    """

    def __init__(self, facet_counts):
        self.dates = facet_counts.get('dates', {})
        self.fields = facet_counts.get('fields', {})
        self.queries = facet_counts.get('queries', {})

        self._total_count = len(self.dates) + len(self.fields) + len(self.queries)

    def get_facets_from(self, x):
        if x not in ('dates', 'queries', 'fields'):
            raise AttributeError('Wrong field, silly.')

        for field, items in getattr(self, x).items():
            for content, count in items:
                if count > 0:
                    yield {'field': field, 'value': content, 'count': count}

    def get_field_facets(self):
        return self.get_facets_from('fields')

    def get_date_facets(self):
        return self.get_facets_from('dates')

    def get_query_facets(self):
        return self.get_facets_from('queries')

    def __bool__(self):
        """
        Used for doing `if facets: print(facets)` - this is the Python 2 magic
        method; __nonzero__ is the equivalent thing in Python 3
        """
        return self._total_count > 0
    __nonzero__ = __bool__

    def __len__(self):
        """
        For checking things via `if len(facets) > 0: print(facets)`
        """
        return self._total_count
