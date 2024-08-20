# Commons Artifact Ingestion Item Model for Scrapy Harvests
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class CollectionItem(Item):
    '''
    The collection an ingestion item belongs to.
    '''

    title = Field()  # Collection title
    id = Field()  # UUID from the collection record
    organization = Field()  # Slug of the org owning this collection.


class HarvestItem(Item):
    '''
    The harvest an ingestion item belongs to.
    '''

    id = Field()  # uuid hex tring
    date = Field()  # datetime.now of when the harvest was created.


class AuthorItem(Item):
    """
    A name and (optional) role of an author or contributor.
    Insert this as an array to ArtifactItem.authors
    """

    name = Field()  # A full person name is used in name.
    role = Field()  # Role can be Editor, Contributor or other generic role


class ThumbnailItem(Item):
    """
    Png, jpg or gif image used for the artifact thumb.
    svg and webp are not supported.
    Can be a thum.io (or other) generator which will then defer the creation to
    ingestion time.  In the case the page or PDF must be web accessible.

    Specify only one or the other of url or url_archive, not both.
    """
    url = Field()  # The location of an image on the web
    url_archive = Field()  # An s3:// URL where the image is archived


class FileItem(Item):
    """
    A FileItem is the unit of retrieval for a Commons Search.
    Multiple files can be associated with an ArtifactItem.
    """

    url = Field()  # The location of the file on the web
    url_archive = Field()  # An s3:// URL where the file is archived
    fulltext_archive = Field()  # An s3:// URL where the full text is archived
    media_type = Field()  # E.g. application/pdf, text/html, text/plain
    language = Field()  # A single language code is accepted
    toc = Field()  # An array of strings, "title|page"


class PropItem(Item):
    """
    A Key-Value object used in props, search_props and hidden_props.
    """

    key = Field()  # Title case label for the value. E.g. 'Pages'
    value = Field()  # Value can be str or int.


class ArtifactItem(Item):
    """
    Metadata for a single Artifact item.
    Copy this to an array of items in the IngestionItem.
    e.g.:
        ingestion_item = IngestionItem()
        artifact_item = ArtifactItem()
        # hydrate your artifact_item...
        artifact_item['title'] = "How to make a commons artifact"
        ingestion_item["artifacts"] = [artifact_item]
    """

    id = Field()  # A uuid str in an IngestionItem
    uri = Field()  # Location of the artifact on the web
    title = Field()  # Artifact title,
    series = Field()  # Series title
    date_updated = Field()  # datetime.now()
    date_published = Field()  # yyyy-mm-dd
    date_circa = Field()  # A date str, used for ranges and circa dates
    publisher = Field()  # Free-form publisher name
    publication_place = Field()  # Free form publication place
    summary = Field()  # Description of the artifact
    type = Field()  # lowercase type value from Commons type schema
    authors = Field()  # Array of AuthorItem values
    thumbnail = Field()  # See ThumbnailItem
    rights = Field()  # Copyright statement
    rights_uri = Field()  # URI to a commons license if applicable
    identifier = Field()  # Local identifier for the item
    issn = Field()  # List of Serial Numbers
    isbn = Field()  # List of Book Numbers
    isbn_online = Field()
    topics = Field()  # Array of tags.  Quote multi-word terms
    languages = Field()  # Array of lang codes
    related_artifacts = Field()  # URIs of related items as an array
    files = Field()  # Array of FileItem
    props = Field()  # Array of PropItems visible to the user.
    search_props = Field()  # Array of PropItems searchable (not visible).
    hidden_props = Field()  # Array of PropItems visible to CMS users.


class IngestionItem(Item):
    """
    This is the root class for an Ingestion payload compatible
    with Coherent Commons.

    Yield this from Spiders as JSON to be compatible with direct ingestion.
    """

    collection = Field()
    harvest = Field()
    artifacts = Field()
