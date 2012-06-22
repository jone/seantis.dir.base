import os
from datetime import datetime

from five import grok
from zope.schema import Text
from zope.schema import TextLine
from zope.schema import List
from zope.interface import Interface
from zope.interface import implements
from zope.app.container.interfaces import IObjectMovedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from plone.directives import form
from plone.directives import dexterity
from plone.dexterity.content import Container
from plone.indexer import indexer
from plone.app.dexterity import browser
from Products.CMFCore.interfaces import IActionSucceededEvent 
from collective.dexteritytextindexer import searchable

from zope.annotation.interfaces import IAttributeAnnotatable
from collective.geo.geographer.interfaces import IGeoreferenceable, IGeoreferenced
from collective.geo.settings.interfaces import IGeoCustomFeatureStyle

from seantis.dir.base import _
from seantis.dir.base import session
from seantis.dir.base import utils

class IDirectoryItemBase(form.Schema):
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


@indexer(IDirectoryItem)
def categoriesIndexer(obj):
    return obj.keywords()


# Subscribe to every event that potentially has an impact on the
# caching in order to trigger a cache invalidation.

@grok.subscribe(IDirectoryItem, IObjectMovedEvent)
def onMovedItem(item, event):
    item.changed(event.oldParent)
    item.changed(event.newParent)

@grok.subscribe(IDirectoryItem, IObjectModifiedEvent)
def onModifiedItem(item, event):
    item.changed(item.parent())

@grok.subscribe(IDirectoryItem, IActionSucceededEvent)
def onChangedWorkflowState(item, event):
    item.changed(item.parent())


class DirectoryItem(Container):
    """Represents objects created using IDirectoryItem."""

    implements(IAttributeAnnotatable, IGeoreferenceable)

    def get_description(self):
        # ensure that the description is never None (which is handled by the
        # interface definition really, but older items were created without
        # the missing_value option and might be different)
        # => yes a migration would be much better, but I lack the nerve
        # of dealing with GenericSetup right now.
        return self.__dict__['description'] or u''

    def set_description(self, value):
        self.__dict__['description'] = value

    description = property(get_description, set_description)

    def parent(self):
        #I tried to use @property here, but this screws with the acquisition
        #context, which apparently is a known sideffect in this case
        return self.aq_inner.aq_parent

    def changed(self, parent):
        """Sets the time when a childitem was changed."""
        if parent:
            self.child_modified = datetime.now()

    def categories(self):
        """Returns a list of tuples with each tuple containing three values:
        [0] = attribute name
        [1] = category label (from parent)
        [2] = category value (from self)

        Only returns actually used categories

        """
        items = []
        labels = self.parent().labels()
        for cat in labels.keys():
            items.append((cat, labels[cat], getattr(self, cat) or u''))
        
        return items

    def keywords(self, categories=None):
        """Returns a flat list of all categories, wheter they are actually
        visible in the directory or not, unless a list of categories is
        specifically passed.

        """
        categories = categories or self.parent().all_categories()
        values = []
        for cat in categories:
            values.append(getattr(self, cat))

        return list(utils.flatten(values))

    def html_description(self):
        """Returns the description with newlines replaced by <br/> tags"""
        return self.description and self.description.replace('\n', '<br />') or ''

    def has_mapdata(self):
        return IGeoreferenced(self).type != None

class DirectoryItemGeoStyleAdapter(grok.Adapter):

    grok.context(IDirectoryItemBase)
    grok.provides(IGeoCustomFeatureStyle)

    use_custom_styles = True
    map_viewlet_position = u"fake-manager"
    linewidth = 2.0
    polygoncolor = u"ff0003c"
    marker_image_size = 0.71875 #23px (image size) / 32px
    display_properties = []

    def __init__(self, context):
        self.context = context

    @property
    def marker_image(self):
        imageurl = utils.get_marker(self.context)
        return 'string:' + imageurl

    def get(self, attribute, default):
        if not hasattr(self, attribute):
            return default
        return getattr(self, attribute)

    def set(self, attribute, value):
        return setattr(self, attribute, value)

    def __getitem__(self, attribute):
        return getattr(self, attribute)

    def setStyles(self, *args):
        pass

    @property
    def geostyles(self):
        return self

def label_widgets(directory, widgets):
    """Takes a list of widgets and substitutes the labels of those representing
    category values with the labels from the Directory. 

    """
    # Set correct label depending on the DirectoryItem value
    labels = directory.labels()
    for field, widget in widgets.items():
        if field in labels:
            widget.label = labels[field]

def remove_unused_widgets(directory, widgets):
    """Takes a list of widgets and removes all representing categories that
    are unused in the given Directory. 

    """
    # Remove unused categories from form
    unused = directory.unused_categories()
    for key in unused:
        del widgets[key]

def get_container_template():
    """Returns the path to the default template for dexterity container items.
    (See lengthy comment in the View class below)
    """
    folder = os.path.dirname(browser.__file__)
    template = os.path.join(folder, 'container.pt')

    assert(os.path.exists(template))

    return template

class DirectoryWidgetUpdate(object):
    def updateWidgets(self):
        """ Updates the widgets with the labels from the parent and removes
        the fields which are not used.

        """
        super(DirectoryWidgetUpdate, self).updateWidgets()
        label_widgets(self.context, self.widgets)
        remove_unused_widgets(self.context, self.widgets)


class View(DirectoryWidgetUpdate, dexterity.DisplayForm):
    """Default view."""
    grok.context(IDirectoryItemBase)
    grok.require('zope2.View')
    
    # This is extremely hackish, but I have yet to find another way. I'd like
    # to completely use the default Dexterity content view, but override the
    # widgets just like in the other views below. Unfortunately, since the
    # default view is not exactly like the others I need to specify a template
    # in this case. 
    # Since I don't want to have my own template, but use the default one, I
    # get the path to said template by figuring out the path to it relative to
    # the plone.app.dexterity.browser module. 
    # Should said path change I'm screwed, so I see this as a temporary solution
    # until I find something better. For now it works as expected :D
    template = grok.PageTemplateFile(get_container_template())


class AddForm(DirectoryWidgetUpdate, dexterity.AddForm):
    """Default add view."""
    grok.context(IDirectoryItem)
    grok.name('seantis.dir.base.item')


class EditForm(DirectoryWidgetUpdate, dexterity.EditForm):
    """Default edit view."""
    grok.context(IDirectoryItem)

class DirectoryItemViewletManager(grok.ViewletManager):
    grok.context(Interface)
    grok.name('seantis.dir.base.item.viewletmanager')

class DirectoryItemViewlet(grok.Viewlet):
    grok.context(IDirectoryItemBase)
    grok.name('seantis.dir.base.item.detail')
    grok.require('zope2.View')
    grok.viewletmanager(DirectoryItemViewletManager)

    template = grok.PageTemplate(u'<p tal:content="context/description" />')
