from zope.interface import Interface
from zope.schema import (
    Text,
    TextLine,
    List,
    Datetime,
    Bool
)

from plone.directives import form
from collective.dexteritytextindexer import searchable

from seantis.dir.base import _

class IDirectoryRoot(form.Schema):
    """Root interface for directories and items alike."""

class IDirectoryBase(IDirectoryRoot):
    """Container for all directory items."""

    title = TextLine(
            title=_(u'Name'),
        )

    subtitle = TextLine(
            title=_(u'Subtitle'),
            required=False
        )
    
    description = Text(
            title=_(u'Description'),
            required=False,
            default=u''
        )
    
    cat1 = TextLine(
            title=_(u'1st Category Name'),
            required=False,
            default=u''
        )

    cat2 = TextLine(
            title=_(u'2nd Category Name'),
            required=False,
            default=u''
        )

    cat3 = TextLine(
            title=_(u'3rd Category Name'),
            required=False,
            default=u''
        )

    cat4 = TextLine(
            title=_(u'4th Category Name'),
            required=False,
            default=u''
        )

    child_modified = Datetime(
            title=_(u'Last time a DirectoryItem was modified'),
            required=False,
            readonly=True
        )

    enable_filter = Bool(
            title=_(u'Enable filtering'),
            required=True,
            default=True
        )

    enable_search = Bool(
            title=_(u'Enable searching'),
            required=True,
            default=True
        )

class IDirectory(IDirectoryBase):
    pass

class IDirectoryItemBase(IDirectoryRoot):
    """Single entry of a directory. Usually you would not want to directly
    work with this class. Instead refer to IDirectoryItem below.

    """

    searchable('title')
    title = TextLine(
            title=_(u'Name'),
        )

    searchable('description')
    description = Text(
            title=_(u'Description'),
            required=False,
            default=u'',
            missing_value=u''
        )

    searchable('cat1')
    cat1 = List(
            title=_(u'1st Category Name'),
            description=_(u'Start typing and select a category. To add a new category write the name and hit enter.'),
            value_type=TextLine(),
            required=False,
        )

    searchable('cat2')
    cat2 = List(
            title=_(u'2nd Category Name'),
            description=_(u'Start typing and select a category. To add a new category write the name and hit enter.'),
            value_type=TextLine(),
            required=False,
        )

    searchable('cat3')
    cat3 = List(
            title=_(u'3rd Category Name'),
            description=_(u'Start typing and select a category. To add a new category write the name and hit enter.'),
            value_type=TextLine(),
            required=False,
        )

    searchable('cat4')
    cat4 = List(
            title=_(u'4th Category Name'),
            description=_(u'Start typing and select a category. To add a new category write the name and hit enter.'),
            value_type=TextLine(),
            required=False,
        )

class IDirectoryItem(IDirectoryItemBase):
    """Marker interface for IDirectory. Exists foremostely to allow
    the overriding of adapters/views in seantis.dir.base. (Given a 
    number of adapters the most specific is used. So if there's an 
    adapter for IDirectoryItem and IDirectoryItemBase, the former
    takes precedence.

    """

class IDirectoryCatalog(Interface):
    """Describes the adapter interface for directory objects that deals
    with iterating over directory items."""

    def items(self):
        """Returns the items of the directory. Those items aren't required
        to actually exist in the ZODB."""

    def filter(self, term):
        """Returns the items filtered by the term. The term is a dictionary
        of categories with the values being strings to search for.

        e.g.

        term=dict(cat1='category-value-1', cat2='category-value-2')

        If the value is equal to '!empty', the category is not searched.
        This is a bit of a relic and might be dropped in the future.
        In fact, these two terms should yield the exact same result:

        1: dict(cat1='category-value-1', cat2='!empty')
        2: dict(cat1='category-value-1')

        """

    def search(self, text):
        """Returns a list of items that turn up in the fulltext search."""

    def sortkey(self):
        """Returns a sort keyfunction to sort the items of the catalog. """

class IFieldMapExtender(Interface):
    """Interface describing an object which can extend the FieldMap class used
    for xlsimport/xlsexport.

    """
    def extend_import(self):
        """Extends the fieldmap with custom fields. The default fieldmap for
        the directory item is set as context.

        """

class IMapMarker(Interface):
    """Interface for providing the URL of the marker image on the map."""
    def url(self, letter):
        """
        Returns the absolute URL of the marker image.
        """
