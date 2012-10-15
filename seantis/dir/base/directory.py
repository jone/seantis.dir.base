import json

from five import grok
from zope.interface import Interface
from plone.directives import form
from plone.dexterity.content import Container
from Products.CMFPlone.PloneBatch import Batch
from plone.app.layout.viewlets.interfaces import IBelowContentTitle

from seantis.dir.base import core
from seantis.dir.base import catalog
from seantis.dir.base import utils
from seantis.dir.base import session
from seantis.dir.base.const import CATEGORIES, ITEMSPERPAGE

from seantis.dir.base.interfaces import IDirectoryItemBase, IDirectoryBase

class Directory(Container):
    """Represents objects created using IDirectory."""

    def all_categories(self):
        """Return a list with the names of all category attributes."""
        return CATEGORIES

    def used_categories(self):
        """Return names of all used (non-empty) category attributes."""
        return [c for c in self.all_categories() if getattr(self, c)]
    
    def unused_categories(self):
        """Return names of all unused (empty) category attributes."""
        return [c for c in self.all_categories() if not getattr(self, c)]

    def labels(self):
        """Return a dictionary with they key being the category attribute
        name and the value being the label defined by the attribute value.
        Returns only used categories, as unused ones don't have labels.

        """
        categories = self.used_categories()
        titles = [getattr(self, c) for c in categories]

        return dict(zip(categories, titles))

    def html_description(self):
        """Returns the description with newlines replaced by <br/> tags"""
        return self.description and self.description.replace('\n', '<br />') or ''

class DirectorySearchViewlet(grok.Viewlet):

    grok.name('seantis.dir.base.DirectorySearchViewlet')
    grok.context(form.Schema)
    grok.require('zope2.View')
    grok.viewletmanager(IBelowContentTitle)

    _template = grok.PageTemplateFile('templates/search.pt')

    def get_context(self, context):
        if IDirectoryBase.providedBy(self.context):
            return IDirectoryBase(self.context)
        elif IDirectoryItemBase.providedBy(self.context):
            if hasattr(IDirectoryItemBase(self.context), 'parent'):
                return IDirectoryItemBase(self.context).parent()
        
        return None

    @property
    def url(self):
        return self.context.absolute_url()

    def remove_count(self, text):
        return utils.remove_count(text);

    @property
    def widths(self):
        if self.context.enable_search and self.context.enable_filter:
            return (40, 60)
        elif self.context.enable_search:
            return (100, 0)
        elif self.context.enable_filter:
            return (0, 100)
        else:
            return (0, 0)

    @property
    def searchstyle(self):
        return 'width: %s%%' % self.widths[0]

    @property
    def filterstyle(self):
        return 'width: %s%%' % self.widths[1]

    def update(self, **kwargs):
        self.context = self.get_context(self.context)
        
        if self.context: 
            self.items = catalog.items(self.context)

            self.values = catalog.grouped_possible_values_counted(
                          self.context, self.items)
            self.labels = self.context.labels()
            self.select = session.get_last_filter(self.context)
            self.searchtext = session.get_last_search(self.context)

    def render(self, **kwargs):
        if self.context != None:
            return self._template.render(self)
        else:
            return u''

    def available(self):
        # grok.Viewlet does provide a way to indicate if the viewlet should be 
        # rendered or not (called between update and render). Unfortunately it is 
        # not used in versions prior to 1.9 which is quite new. 
        # For this reason the render method above is used instead of just 
        # specifying self.template. Once 1.9+ of grokcore.viewlet is widely used
        # self._template can be renamed to self.template and the render method 
        # can be removed.
        return self.get_context(self.context) != None


class View(core.View):
    """Default view of Directory."""

    grok.context(IDirectoryBase)
    grok.require('zope2.View')
    
    template = grok.PageTemplateFile('templates/directory.pt')
    
    categories, items, values = None, None, None

    def filter(self, terms):
        if terms:
            self.items = catalog.category_filter(self.context, terms)
        session.set_last_filter(self.context, terms)

    def search(self, searchtext):
        if searchtext:
            self.items = catalog.fulltext_search(self.context, searchtext)
        session.set_last_search(self.context, searchtext)

    def reset(self, *args):
        session.reset_search_filter(self.context)

    def primary_action(self):
        action, param = None, None
        if 'reset' in self.request.keys():
            action = self.reset
            param = None
        elif 'search' in self.request.keys():
            action = self.search
            param = self.request.get('searchtext')
        elif 'filter' in self.request.keys():
            action = self.filter
            param = self.get_filter_terms()
        else:
            searchtext = session.get_last_search(self.context)
            terms = session.get_last_filter(self.context)
            if searchtext:
                action = self.search
                param = searchtext
            elif terms:
                action = self.filter
                param = terms
        
        if not action:
            action = lambda param: None
            
        return action, param

    @property
    def filtered(self):
        return len(self.items) != self.unfiltered_count

    def update(self, **kwargs):
        self.items = catalog.items(self.context)
        self.unfiltered_count = len(self.items)
        self.values = catalog.grouped_possible_values_counted(
                      self.context, self.items)
        self.labels = self.context.labels()

        action, param = self.primary_action()
        action(param)

        super(View, self).update(**kwargs)

    def category_values(self, category, filtered=True):
        """ Returns all possible values of the given category (1-4). 
        If filtered is True, only the items matching the current filter/search
        are considered.
        """

        assert category in (1, 2, 3, 4)
        category = 'cat%i' % category

        items = filtered and self.items or catalog.items(self.context)
        grouped = catalog.grouped_possible_values(
            self.context, items, categories=[category]
        )

        return sorted(grouped[category].keys())

    @property
    def batch(self):
        start = int(self.request.get('b_start') or 0)
        return Batch(self.items, ITEMSPERPAGE, start, orphan=1)

class JsonFilterView(core.View):
    """View to filter the catalog with ajax."""

    grok.context(IDirectoryBase)
    grok.require('zope2.View')
    grok.name('filter')

    def render(self, **kwargs):
        terms = self.get_filter_terms()

        if not len(terms.keys()):
            return json.dumps({})

        items = catalog.category_filter(self.context, terms)
        result = catalog.grouped_possible_values_counted(self.context, items)
        return json.dumps(result)


class JsonSearch(core.View):
    """View to search for a category using the jquery tokenizer plugin."""

    grok.context(IDirectoryBase)
    grok.require('zope2.View')
    grok.name('query')

    def render(self, **kwargs):
        category = 'cat%i' % int(self.request['cat'])

        if not category in CATEGORIES:
            return json.dumps([])

        directory = self.context
        possible = catalog.grouped_possible_values(directory, catalog.items(directory))
        possible = possible[category].keys()

        query = self.request['q']

        if not query:
            json.dumps([dict(id=val, name=val) for val in possible])

        searchtext = unicode(query.lower().decode('utf-8'))
        filterfn = lambda item: searchtext in item.lower()
        filtered = filter(filterfn, possible)
        
        return json.dumps([dict(id=val, name=val) for val in filtered])

class DirectoryViewletManager(grok.ViewletManager):
    grok.context(Interface)
    grok.name('seantis.dir.base.directory.viewletmanager')