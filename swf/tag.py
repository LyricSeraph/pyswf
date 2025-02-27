from __future__ import absolute_import
from .consts import *
from .data import *
from .utils import *
from .stream import *
import datetime
from six.moves import range
try:
    import Image
except ImportError:
    from PIL import Image
import struct
from io import BytesIO


class TagFactory(object):
    @classmethod
    def create(cls, type):
        """ Return the created tag by specifying an integer """
        if type == 0: return TagEnd()
        elif type == 1: return TagShowFrame()
        elif type == 2: return TagDefineShape()
        elif type == 4: return TagPlaceObject()
        elif type == 5: return TagRemoveObject()
        elif type == 6: return TagDefineBits()
        elif type == 7: return TagDefineButton()
        elif type == 8: return TagJPEGTables()
        elif type == 9: return TagSetBackgroundColor()
        elif type == 10: return TagDefineFont()
        elif type == 11: return TagDefineText()
        elif type == 12: return TagDoAction()
        elif type == 13: return TagDefineFontInfo()
        elif type == 14: return TagDefineSound()
        elif type == 15: return TagStartSound()
        elif type == 17: return TagDefineButtonSound()
        elif type == 18: return TagSoundStreamHead()
        elif type == 19: return TagSoundStreamBlock()
        elif type == 20: return TagDefineBitsLossless()
        elif type == 21: return TagDefineBitsJPEG2()
        elif type == 22: return TagDefineShape2()
        elif type == 24: return TagProtect()
        elif type == 26: return TagPlaceObject2()
        elif type == 28: return TagRemoveObject2()
        elif type == 32: return TagDefineShape3()
        elif type == 33: return TagDefineText2()
        elif type == 34: return TagDefineButton2()
        elif type == 35: return TagDefineBitsJPEG3()
        elif type == 36: return TagDefineBitsLossless2()
        elif type == 37: return TagDefineEditText()
        elif type == 39: return TagDefineSprite()
        elif type == 41: return TagProductInfo()
        elif type == 43: return TagFrameLabel()
        elif type == 45: return TagSoundStreamHead2()
        elif type == 46: return TagDefineMorphShape()
        elif type == 48: return TagDefineFont2()
        elif type == 56: return TagExportAssets()
        elif type == 58: return TagEnableDebugger()
        elif type == 59: return TagDoInitAction()
        elif type == 60: return TagDefineVideoStream()
        elif type == 61: return TagVideoFrame()
        elif type == 63: return TagDebugID()
        elif type == 64: return TagEnableDebugger2()
        elif type == 65: return TagScriptLimits()
        elif type == 69: return TagFileAttributes()
        elif type == 70: return TagPlaceObject3()
        elif type == 72: return TagDoABCDefine()
        elif type == 73: return TagDefineFontAlignZones()
        elif type == 74: return TagCSMTextSettings()
        elif type == 75: return TagDefineFont3()
        elif type == 76: return TagSymbolClass()
        elif type == 77: return TagMetadata()
        elif type == 78: return TagDefineScalingGrid()
        elif type == 82: return TagDoABC()
        elif type == 83: return TagDefineShape4()
        elif type == 84: return TagDefineMorphShape2()
        elif type == 86: return TagDefineSceneAndFrameLabelData()
        elif type == 87: return TagDefineBinaryData()
        elif type == 88: return TagDefineFontName()
        elif type == 89: return TagStartSound2()
        else: return None

class Tag(object):
    def __init__(self):
        pass

    @property
    def level(self):
        return 1

    @property
    def version(self):
        return 1

    @property
    def name(self):
        """ The tag name """
        return ""

    def parse(self, data, length, version=1):
        """ Parses this tag """
        pass

    def get_dependencies(self):
        """ Returns the character ids this tag refers to """
        return set()

    def __str__(self):
        return "[%02d:%s]" % (self.type, self.name)

class DefinitionTag(Tag):

    def __init__(self):
        super(DefinitionTag, self).__init__()
        self._characterId = -1

    @property
    def characterId(self):
        """ Return the character ID """
        return self._characterId

    @characterId.setter
    def characterId(self, value):
        """ Sets the character ID """
        self._characterId = value

    def parse(self, data, length, version=1):
        pass

    def get_dependencies(self):
        s = super(DefinitionTag, self).get_dependencies()
        s.add(self.characterId)
        return s

class DisplayListTag(Tag):
    characterId = -1
    def __init__(self):
        super(DisplayListTag, self).__init__()

    def parse(self, data, length, version=1):
        pass

    def get_dependencies(self):
        s = super(DisplayListTag, self).get_dependencies()
        s.add(self.characterId)
        return s

class SWFTimelineContainer(DefinitionTag):
    def __init__(self):
        self.tags = []
        super(SWFTimelineContainer, self).__init__()

    def get_dependencies(self):
        """ Returns the character ids this tag refers to """
        s = super(SWFTimelineContainer, self).get_dependencies()
        for dt in self.all_tags_of_type((DefinitionTag, TagPlaceObject)):
            s.update(dt.get_dependencies())
        return s

    def parse_tags(self, data, version=1):
        pos = data.tell()
        self.file_length = self._get_file_length(data, pos)
        tag = None
        while type(tag) != TagEnd:
            tag = self.parse_tag(data)
            if tag:
                #print tag.name
                self.tags.append(tag)

    def parse_tag(self, data):
        pos = data.tell()
        eof = (pos > self.file_length)
        if eof:
            #print "WARNING: end of file encountered, no end tag."
            return TagEnd()
        raw_tag = data.readraw_tag()
        tag_type = raw_tag.header.type
        tag = TagFactory.create(tag_type)
        if tag is not None:
            #print tag.name
            data.seek(raw_tag.pos_content)
            data.reset_bits_pending()
            tag.parse(data, raw_tag.header.content_length, tag.version)
            #except:
            #    print "=> tag_error", tag.name
            data.seek(pos + raw_tag.header.tag_length)
        else:
            #print "[WARNING] unhandled tag %s" % (hex(tag_type))
            data.skip_bytes(raw_tag.header.tag_length)
        data.seek(pos + raw_tag.header.tag_length)
        return tag

    def _get_file_length(self, data, pos):
        data.f.seek(0, 2)
        length = data.tell()
        data.f.seek(pos)
        return length

    def all_tags_of_type(self, type_or_types, recurse_into_sprites = True):
        """
        Generator for all tags of the given type_or_types.

        Generates in breadth-first order, optionally including all sub-containers.
        """
        for t in self.tags:
            if isinstance(t, type_or_types):
                yield t
        if recurse_into_sprites:
            for t in self.tags:
                # recurse into nested sprites
                if isinstance(t, SWFTimelineContainer):
                    for containedtag in t.all_tags_of_type(type_or_types):
                        yield containedtag

    def build_dictionary(self):
        """
        Return a dictionary of characterIds to their defining tags.
        """
        d = {}
        for t in self.all_tags_of_type(DefinitionTag, recurse_into_sprites = False):
            if t.characterId in d:
                #print 'redefinition of characterId %d:' % (t.characterId)
                #print '  was:', d[t.characterId]
                #print 'redef:', t
                raise ValueError('illegal redefinition of character')
            d[t.characterId] = t
        return d

    def collect_sound_streams(self):
        """
        Return a list of sound streams in this timeline and its children.
        The streams are returned in order with respect to the timeline.

        A stream is returned as a list: the first element is the tag
        which introduced that stream; other elements are the tags
        which made up the stream body (if any).
        """
        rc = []
        current_stream = None
        # looking in all containers for frames
        for tag in self.all_tags_of_type((TagSoundStreamHead, TagSoundStreamBlock)):
            if isinstance(tag, TagSoundStreamHead):
                # we have a new stream
                current_stream = [ tag ]
                rc.append(current_stream)
            if isinstance(tag, TagSoundStreamBlock):
                # we have a frame for the current stream
                current_stream.append(tag)
        return rc

    def collect_video_streams(self):
        """
        Return a list of video streams in this timeline and its children.
        The streams are returned in order with respect to the timeline.

        A stream is returned as a list: the first element is the tag
        which introduced that stream; other elements are the tags
        which made up the stream body (if any).
        """
        rc = []
        streams_by_id = {}

        # scan first for all streams
        for t in self.all_tags_of_type(TagDefineVideoStream):
            stream = [ t ]
            streams_by_id[t.characterId] = stream
            rc.append(stream)

        # then find the frames
        for t in self.all_tags_of_type(TagVideoFrame):
            # we have a frame for the /named/ stream
            assert t.streamId in streams_by_id
            streams_by_id[t.streamId].append(t)

        return rc

class TagEnd(Tag):
    """
    The End tag marks the end of a file. This must always be the last tag in a file.
    The End tag is also required to end a sprite definition.
    The minimum file format version is SWF 1.
    """
    TYPE = 0
    def __init__(self):
        super(TagEnd, self).__init__()

    @property
    def name(self):
        """ The tag name """
        return "End"

    @property
    def type(self):
        return TagEnd.TYPE

    def __str__(self):
        return "[%02d:%s]" % (self.type, self.name)

class TagShowFrame(Tag):
    """
    The ShowFrame tag instructs Flash Player to display the contents of the
    display list. The file is paused for the duration of a single frame.
    The minimum file format version is SWF 1.
    """
    TYPE = 1
    def __init__(self):
        super(TagShowFrame, self).__init__()

    @property
    def name(self):
        return "ShowFrame"

    @property
    def type(self):
        return TagShowFrame.TYPE

    def __str__(self):
        return "[%02d:%s]" % (self.type, self.name)

class TagDefineShape(DefinitionTag):
    """
    The DefineShape tag defines a shape for later use by control tags such as
    PlaceObject. The ShapeId uniquely identifies this shape as 'character' in
    the Dictionary. The ShapeBounds field is the rectangle that completely
    encloses the shape. The SHAPEWITHSTYLE structure includes all the paths,
    fill styles and line styles that make up the shape.
    The minimum file format version is SWF 1.
    """
    TYPE = 2

    def __init__(self):
        self._shapes = None
        self._shape_bounds = None
        super(TagDefineShape, self).__init__()

    @property
    def name(self):
        return "DefineShape"

    @property
    def type(self):
        return TagDefineShape.TYPE

    @property
    def shapes(self):
        """ Return SWFShape """
        return self._shapes

    @property
    def shape_bounds(self):
        """ Return the bounds of this tag as a SWFRectangle """
        return self._shape_bounds

    def export(self, handler=None):
        """ Export this tag """
        return self.shapes.export(handler)

    def parse(self, data, length, version=1):
        self.characterId = data.readUI16()
        self._shape_bounds = data.readRECT()
        self._shapes = data.readSHAPEWITHSTYLE(self.level)

    def get_dependencies(self):
        s = super(TagDefineShape, self).get_dependencies()
        s.update(self.shapes.get_dependencies())
        return s

    def __str__(self):
        s = super(TagDefineShape, self).__str__( ) + " " + \
            "ID: %d" % self.characterId + ", " + \
            "Bounds: " + self._shape_bounds.__str__()
        #s += "\n%s" % self._shapes.__str__()
        return s

class TagPlaceObject(DisplayListTag):
    """
    The PlaceObject tag adds a character to the display list. The CharacterId
    identifies the character to be added. The Depth field specifies the
    stacking order of the character. The Matrix field species the position,
    scale, and rotation of the character. If the size of the PlaceObject tag
    exceeds the end of the transformation matrix, it is assumed that a
    ColorTransform field is appended to the record. The ColorTransform field
    specifies a color effect (such as transparency) that is applied to the character.
    The same character can be added more than once to the display list with
    a different depth and transformation matrix.
    """
    TYPE = 4
    hasClipActions = False
    hasClipDepth = False
    hasName = False
    hasRatio = False
    hasColorTransform = False
    hasMatrix = False
    hasCharacter = False
    hasMove = False
    hasImage = False
    hasClassName = False
    hasCacheAsBitmap = False
    hasBlendMode = False
    hasFilterList = False
    depth = 0
    matrix = None
    colorTransform = None
    # Forward declarations for TagPlaceObject2
    ratio = 0
    instanceName = None
    clipDepth = 0
    clipActions = None
    # Forward declarations for TagPlaceObject3
    className = None
    blendMode = 0
    bitmapCache = 0

    def __init__(self):
        self._surfaceFilterList = []
        super(TagPlaceObject, self).__init__()

    def parse(self, data, length, version=1):
        """ Parses this tag """
        pos = data.tell()
        self.characterId = data.readUI16()
        self.depth = data.readUI16();
        self.matrix = data.readMATRIX();
        self.hasCharacter = True;
        self.hasMatrix = True;
        if data.tell() - pos < length:
            colorTransform = data.readCXFORM()
            self.hasColorTransform = True

    def get_dependencies(self):
        s = super(TagPlaceObject, self).get_dependencies()
        if self.hasCharacter:
            s.add(self.characterId)
        return s

    @property
    def filters(self):
        """ Returns a list of filter """
        return self._surfaceFilterList

    @property
    def name(self):
        return "PlaceObject"

    @property
    def type(self):
        return TagPlaceObject.TYPE

    def __str__(self):
        s = super(TagPlaceObject, self).__str__() + " " + \
            "Depth: %d, " % self.depth + \
            "CharacterID: %d" % self.characterId
        if self.hasName:
            s+= ", InstanceName: %s" % self.instanceName
        if self.hasMatrix:
            s += ", Matrix: %s" % self.matrix.__str__()
        if self.hasClipDepth:
            s += ", ClipDepth: %d" % self.clipDepth
        if self.hasColorTransform:
            s += ", ColorTransform: %s" % self.colorTransform.__str__()
        if self.hasFilterList:
            s += ", Filters: %d" % len(self.filters)
        if self.hasBlendMode:
            s += ", Blendmode: %d" % self.blendMode
        return s

class TagRemoveObject(DisplayListTag):
    """
    The RemoveObject tag removes the specified character (at the specified depth)
    from the display list.
    The minimum file format version is SWF 1.
    """
    TYPE = 5
    depth = 0
    def __init__(self):
        super(TagRemoveObject, self).__init__()

    @property
    def name(self):
        return "RemoveObject"

    @property
    def type(self):
        return TagRemoveObject.TYPE

    def parse(self, data, length, version=1):
        """ Parses this tag """
        self.characterId = data.readUI16()
        self.depth = data.readUI16()

class TagDefineBits(DefinitionTag):
    """
    This tag defines a bitmap character with JPEG compression. It contains only
    the JPEG compressed image data (from the Frame Header onward). A separate
    JPEGTables tag contains the JPEG encoding data used to encode this image
    (the Tables/Misc segment).
    NOTE:
        Only one JPEGTables tag is allowed in a SWF file, and thus all bitmaps
        defined with DefineBits must share common encoding tables.
    The data in this tag begins with the JPEG SOI marker 0xFF, 0xD8 and ends
    with the EOI marker 0xFF, 0xD9. Before version 8 of the SWF file format,
    SWF files could contain an erroneous header of 0xFF, 0xD9, 0xFF, 0xD8 before
    the JPEG SOI marker.
    """
    TYPE = 6
    bitmapData = None
    def __init__(self):
        self.bitmapData = BytesIO()
        self.bitmapType = BitmapType.JPEG
        super(TagDefineBits, self).__init__()

    @property
    def name(self):
        return "DefineBits"

    @property
    def type(self):
        return TagDefineBits.TYPE

    def parse(self, data, length, version=1):
        self.bitmapData = BytesIO()
        self.characterId = data.readUI16()
        if length > 2:
            self.bitmapData.write(data.f.read(length - 2))
            self.bitmapData.seek(0)

class TagJPEGTables(DefinitionTag):
    """
    This tag defines the JPEG encoding table (the Tables/Misc segment) for all
    JPEG images defined using the DefineBits tag. There may only be one
    JPEGTables tag in a SWF file.
    The data in this tag begins with the JPEG SOI marker 0xFF, 0xD8 and ends
    with the EOI marker 0xFF, 0xD9. Before version 8 of the SWF file format,
    SWF files could contain an erroneous header of 0xFF, 0xD9, 0xFF, 0xD8 before
    the JPEG SOI marker.
    The minimum file format version for this tag is SWF 1.
    """
    TYPE = 8
    jpegTables = None
    length = 0

    def __init__(self):
        super(TagJPEGTables, self).__init__()
        self.jpegTables = BytesIO()

    @property
    def name(self):
        return "JPEGTables"

    @property
    def type(self):
        return TagJPEGTables.TYPE

    def parse(self, data, length, version=1):
        self.length = length
        if length > 0:
            self.jpegTables.write(data.f.read(length))
            self.jpegTables.seek(0)

    def __str__(self):
        s = super(TagJPEGTables, self).__str__()
        s += " Length: %d" % self.length
        return s

class TagSetBackgroundColor(Tag):
    """
    The SetBackgroundColor tag sets the background color of the display.
    The minimum file format version is SWF 1.
    """
    TYPE = 9
    color = 0
    def __init__(self):
        super(TagSetBackgroundColor, self).__init__()

    def parse(self, data, length, version=1):
        self.color = data.readRGB()

    @property
    def name(self):
        return "SetBackgroundColor"

    @property
    def type(self):
        return TagSetBackgroundColor.TYPE

    def __str__(self):
        s = super(TagSetBackgroundColor, self).__str__()
        s += " Color: " + ColorUtils.to_rgb_string(self.color)
        return s

class TagDefineFont(DefinitionTag):
    """
    The DefineFont tag defines the shape outlines of each glyph used in a
    particular font. Only the glyphs that are used by subsequent DefineText
    tags are actually defined.
    DefineFont tags cannot be used for dynamic text. Dynamic text requires
    the DefineFont2 tag.
    The minimum file format version is SWF 1.
    """
    TYPE = 10
    offsetTable = []
    glyphShapeTable = []
    def __init__(self):
        super(TagDefineFont, self).__init__()

    @property
    def name(self):
        return "DefineFont"

    @property
    def type(self):
        return TagDefineFont.TYPE

    @property
    def level(self):
        return 1

    @property
    def version(self):
        return 1

    @property
    def unitDivisor(self):
        return 1

    def parse(self, data, length, version=1):
        self.glyphShapeTable = []
        self.offsetTable = []
        self.characterId = data.readUI16()

        # Because the glyph shape table immediately follows the offset table,
        # the number of entries in each table (the number of glyphs in the
        # font) can be inferred by dividing the first entry in the offset
        # table by two.
        self.offsetTable.append(data.readUI16())
        numGlyphs = self.offsetTable[0] / 2

        for i in range(1, numGlyphs):
            self.offsetTable.append(data.readUI16())

        for i in range(numGlyphs):
            self.glyphShapeTable.append(data.readSHAPE(self.unitDivisor))

class TagDefineText(DefinitionTag):
    """
    The DefineText tag defines a block of static text. It describes the font,
    size, color, and exact position of every character in the text object.
    The minimum file format version is SWF 1.
    """
    TYPE = 11
    textBounds = None
    textMatrix = None

    def __init__(self):
        self._records = []
        super(TagDefineText, self).__init__()

    @property
    def name(self):
        return "TagDefineText"

    @property
    def type(self):
        return TagDefineText.TYPE

    @property
    def level(self):
        return 1

    @property
    def version(self):
        return 1

    def get_dependencies(self):
        s = super(TagDefineText, self).get_dependencies()
        for r in self.records:
            s.update(r.get_dependencies())
        return s

    @property
    def records(self):
        """ Return list of SWFTextRecord """
        return self._records

    def parse(self, data, length, version=1):
        self._records = []
        self.characterId = data.readUI16()
        self.textBounds = data.readRECT()
        self.textMatrix = data.readMATRIX()
        glyphBits = data.readUI8()
        advanceBits = data.readUI8()
        record = None
        record = data.readTEXTRECORD(glyphBits, advanceBits, record, self.level)
        while not record is None:
            self._records.append(record)
            record = data.readTEXTRECORD(glyphBits, advanceBits, record, self.level)

class TagDoAction(Tag):
    """
    DoAction instructs Flash Player to perform a list of actions when the
    current frame is complete. The actions are performed when the ShowFrame
    tag is encountered, regardless of where in the frame the DoAction tag appears.
    Starting with SWF 9, if the ActionScript3 field of the FileAttributes tag is 1,
    the contents of the DoAction tag will be ignored.
    """
    TYPE = 12
    def __init__(self):
        self._actions = []
        super(TagDoAction, self).__init__()

    @property
    def name(self):
        return "DoAction"

    @property
    def type(self):
        """ Return the SWF tag type """
        return TagDoAction.TYPE

    @property
    def level(self):
        return 1

    @property
    def version(self):
        """ Return the minimum SWF version """
        return 3

    @property
    def actions(self):
        """ Return list of SWFActionRecord """
        return self._actions

    def parse(self, data, length, version=1):
        self._actions = data.readACTIONRECORDs()

class TagDefineFontInfo(Tag):
    """
    The DefineFontInfo tag defines a mapping from a glyph font (defined with DefineFont) to a
    device font. It provides a font name and style to pass to the playback platform's text engine,
    and a table of character codes that identifies the character represented by each glyph in the
    corresponding DefineFont tag, allowing the glyph indices of a DefineText tag to be converted
    to character strings.
    The presence of a DefineFontInfo tag does not force a glyph font to become a device font; it
    merely makes the option available. The actual choice between glyph and device usage is made
    according to the value of devicefont (see the introduction) or the value of UseOutlines in a
    DefineEditText tag. If a device font is unavailable on a playback platform, Flash Player will
    fall back to glyph text.
    """
    TYPE = 13
    def __init__(self):
        super(TagDefineFontInfo, self).__init__()

    @property
    def name(self):
        return "DefineFontInfo"

    @property
    def type(self):
        return TagDefineFontInfo.TYPE

    @property
    def level(self):
        return 1

    @property
    def version(self):
        return 1

    @property
    def unitDivisor(self):
        return 1

    def get_dependencies(self):
        s = super(TagDefineFontInfo, self).get_dependencies()
        s.add(self.characterId)
        return s

    def parse(self, data, length, version=1):
        self.codeTable = []

        # FontID
        self.characterId = data.readUI16()

        fontNameLen = data.readUI8()

        self.fontName = ""
        self.useGlyphText = False

        # Read in font name, one character at a time. If any of the
        # characters are non-ASCII, assume that glyph text should be
        # used rather than device text.
        for i in range(fontNameLen):
            ord = data.readUI8()

            if ord in range(128):
                self.fontName += chr(ord)
            else:
                self.useGlyphText = True

        if self.useGlyphText:
            self.fontName = "Font_{0}".format(self.characterId)

        flags = data.readUI8()

        self.smallText = ((flags & 0x20) != 0)
        self.shiftJIS = ((flags & 0x10) != 0)
        self.ansi  = ((flags & 0x08) != 0)
        self.italic = ((flags & 0x04) != 0)
        self.bold = ((flags & 0x02) != 0)
        self.wideCodes = ((flags & 0x01) != 0)

        if self.wideCodes:
            numGlyphs = (length - 2 - 1 - fontNameLen - 1) / 2
        else:
            numGlyphs = length - 2 - 1 - fontNameLen - 1

        for i in range(0, numGlyphs):
            self.codeTable.append(data.readUI16() if self.wideCodes else data.readUI8())

class TagDefineBitsLossless(DefinitionTag):
    """
    Defines a lossless bitmap character that contains RGB bitmap data compressed
    with ZLIB. The data format used by the ZLIB library is described by
    Request for Comments (RFCs) documents 1950 to 1952.
    Two kinds of bitmaps are supported. Colormapped images define a colormap of
    up to 256 colors, each represented by a 24-bit RGB value, and then use
    8-bit pixel values to index into the colormap. Direct images store actual
    pixel color values using 15 bits (32,768 colors) or 24 bits (about 17 million colors).
    The minimum file format version for this tag is SWF 2.
    """
    TYPE = 20
    bitmapData = None
    image_buffer = b""
    bitmap_format = 0
    bitmap_width = 0
    bitmap_height = 0
    bitmap_color_size = 0
    zlib_bitmap_data = None
    padded_width = 0
    def __init__(self):
        super(TagDefineBitsLossless, self).__init__()

    def parse(self, data, length, version=1):
        import zlib
        self.image_buffer = b""
        self.characterId = data.readUI16()
        self.bitmap_format = data.readUI8()
        self.bitmap_width = data.readUI16()
        self.bitmap_height = data.readUI16()
        if self.bitmap_format == BitmapFormat.BIT_8:
            self.bitmap_color_size = data.readUI8()
            self.zlib_bitmap_data = data.f.read(length-8)
        else:
            self.zlib_bitmap_data = data.f.read(length-7)

        # decompress zlib encoded bytes
        compressed_length = len(self.zlib_bitmap_data)
        zip = zlib.decompressobj()
        temp = BytesIO()
        temp.write(zip.decompress(self.zlib_bitmap_data))
        temp.seek(0, 2)
        uncompressed_length = temp.tell()
        temp.seek(0)

        # padding : should be aligned to 32 bit boundary
        self.padded_width = self.bitmap_width
        while self.padded_width % 4 != 0:
            self.padded_width += 1
        t = self.padded_width * self.bitmap_height

        is_lossless2 = (type(self) == TagDefineBitsLossless2)
        im = None
        self.bitmapData = BytesIO()

        indexed_colors = []
        if self.bitmap_format == BitmapFormat.BIT_8:
            for i in range(0, self.bitmap_color_size + 1):
                r = ord(temp.read(1))
                g = ord(temp.read(1))
                b = ord(temp.read(1))
                a = ord(temp.read(1)) if is_lossless2 else 0xff
                indexed_colors.append(struct.pack("BBBB", r, g, b, a))

            # create the image buffer
            s = BytesIO()
            for i in range(t):
                s.write(indexed_colors[ord(temp.read(1))])
            self.image_buffer = s.getvalue()
            s.close()

            im = Image.frombytes("RGBA", (self.padded_width, self.bitmap_height), self.image_buffer)
            im = im.crop((0, 0, self.bitmap_width, self.bitmap_height))

        elif self.bitmap_format == BitmapFormat.BIT_15:
            raise Exception("DefineBitsLossless: BIT_15 not yet implemented")
        elif self.bitmap_format == BitmapFormat.BIT_24:
            # we have no padding, since PIX24s are 32-bit aligned
            t = self.bitmap_width * self.bitmap_height
            # read PIX24's
            s = BytesIO()
            for i in range(0, t):
                if not is_lossless2:
                    temp.read(1) # reserved, always 0
                a = ord(temp.read(1)) if is_lossless2 else 0xff
                r = ord(temp.read(1))
                g = ord(temp.read(1))
                b = ord(temp.read(1))
                s.write(struct.pack("BBBB", r, g, b, a))
            self.image_buffer = s.getvalue()
            im = Image.frombytes("RGBA", (self.bitmap_width, self.bitmap_height), self.image_buffer)
        else:
            raise Exception("unhandled bitmap format! %s %d" % (BitmapFormat.tobytes(self.bitmap_format), self.bitmap_format))

        if not im is None:
            im.save(self.bitmapData, "PNG")
            self.bitmapData.seek(0)
            self.bitmapType = ImageUtils.get_image_type(self.bitmapData)

    @property
    def name(self):
        return "DefineBitsLossless"

    @property
    def type(self):
        return TagDefineBitsLossless.TYPE

class TagDefineBitsJPEG2(TagDefineBits):
    """
    This tag defines a bitmap character with JPEG compression. It differs from
    DefineBits in that it contains both the JPEG encoding table and the JPEG
    image data. This tag allows multiple JPEG images with differing encoding
    tables to be defined within a single SWF file.
    The data in this tag begins with the JPEG SOI marker 0xFF, 0xD8 and ends
    with the EOI marker 0xFF, 0xD9. Before version 8 of the SWF file format,
    SWF files could contain an erroneous header of 0xFF, 0xD9, 0xFF, 0xD8
    before the JPEG SOI marker.
    In addition to specifying JPEG data, DefineBitsJPEG2 can also contain PNG
    image data and non-animated GIF89a image data.

    - If ImageData begins with the eight bytes 0x89 0x50 0x4E 0x47 0x0D 0x0A 0x1A 0x0A,
      the ImageData contains PNG data.
    - If ImageData begins with the six bytes 0x47 0x49 0x46 0x38 0x39 0x61, the ImageData
      contains GIF89a data.

    The minimum file format version for this tag is SWF 2. The minimum file format
    version for embedding PNG of GIF89a data is SWF 8.
    """
    TYPE = 21
    bitmapType = 0

    def __init__(self):
        super(TagDefineBitsJPEG2, self).__init__()

    @property
    def name(self):
        return "DefineBitsJPEG2"

    @property
    def type(self):
        return TagDefineBitsJPEG2.TYPE

    @property
    def version(self):
        return 2 if self.bitmapType == BitmapType.JPEG else 8

    @property
    def level(self):
        return 2

    def parse(self, data, length, version=1):
        super(TagDefineBitsJPEG2, self).parse(data, length, version)
        self.bitmapType = ImageUtils.get_image_type(self.bitmapData)

class TagDefineShape2(TagDefineShape):
    """
    DefineShape2 extends the capabilities of DefineShape with the ability
    to support more than 255 styles in the style list and multiple style
    lists in a single shape.
    The minimum file format version is SWF 2.
    """
    TYPE = 22

    def __init__(self):
        super(TagDefineShape2, self).__init__()

    @property
    def name(self):
        return "DefineShape2"

    @property
    def type(self):
        return TagDefineShape2.TYPE

    @property
    def level(self):
        return 2

    @property
    def version(self):
        return 2

class TagPlaceObject2(TagPlaceObject):
    """
    The PlaceObject2 tag extends the functionality of the PlaceObject tag.
    The PlaceObject2 tag can both add a character to the display list, and
    modify the attributes of a character that is already on the display list.
    The PlaceObject2 tag changed slightly from SWF 4 to SWF 5. In SWF 5,
    clip actions were added.
    The tag begins with a group of flags that indicate which fields are
    present in the tag. The optional fields are CharacterId, Matrix,
    ColorTransform, Ratio, ClipDepth, Name, and ClipActions.
    The Depth field is the only field that is always required.
    The depth value determines the stacking order of the character.
    Characters with lower depth values are displayed underneath characters
    with higher depth values. A depth value of 1 means the character is
    displayed at the bottom of the stack. Any given depth can have only one
    character. This means a character that is already on the display list can
    be identified by its depth alone (that is, a CharacterId is not required).
    The PlaceFlagMove and PlaceFlagHasCharacter tags indicate whether a new
    character is being added to the display list, or a character already on the
    display list is being modified. The meaning of the flags is as follows:

    - PlaceFlagMove = 0 and PlaceFlagHasCharacter = 1 A new character
      (with ID of CharacterId) is placed on the display list at the specified
      depth. Other fields set the attributes of this new character.
    - PlaceFlagMove = 1 and PlaceFlagHasCharacter = 0
      The character at the specified depth is modified. Other fields modify the
      attributes of this character. Because any given depth can have only one
      character, no CharacterId is required.
    - PlaceFlagMove = 1 and PlaceFlagHasCharacter = 1
      The character at the specified Depth is removed, and a new character
      (with ID of CharacterId) is placed at that depth. Other fields set the
      attributes of this new character.
      For example, a character that is moved over a series of frames has
      PlaceFlagHasCharacter set in the first frame, and PlaceFlagMove set in
      subsequent frames. The first frame places the new character at the desired
      depth, and sets the initial transformation matrix. Subsequent frames replace
      the transformation matrix of the character at the desired depth.

    The optional fields in PlaceObject2 have the following meaning:
    - The CharacterId field specifies the character to be added to the display list.
      CharacterId is used only when a new character is being added. If a character
      that is already on the display list is being modified, the CharacterId field is absent.
    - The Matrix field specifies the position, scale and rotation of the character
      being added or modified.
    - The ColorTransform field specifies the color effect applied to the character
      being added or modified.
    - The Ratio field specifies a morph ratio for the character being added or modified.
      This field applies only to characters defined with DefineMorphShape, and controls
      how far the morph has progressed. A ratio of zero displays the character at the start
      of the morph. A ratio of 65535 displays the character at the end of the morph.
      For values between zero and 65535 Flash Player interpolates between the start and end
      shapes, and displays an in- between shape.
    - The ClipDepth field specifies the top-most depth that will be masked by the character
      being added. A ClipDepth of zero indicates that this is not a clipping character.
    - The Name field specifies a name for the character being added or modified. This field
      is typically used with sprite characters, and is used to identify the sprite for
      SetTarget actions. It allows the main file (or other sprites) to perform actions
      inside the sprite (see 'Sprites and Movie Clips' on page 231).
    - The ClipActions field, which is valid only for placing sprite characters, defines
      one or more event handlers to be invoked when certain events occur.
    """
    TYPE = 26
    def __init__(self):
        super(TagPlaceObject2, self).__init__()

    def parse(self, data, length, version=1):
        flags = data.readUI8()
        self.hasClipActions = (flags & 0x80) != 0
        self.hasClipDepth = (flags & 0x40) != 0
        self.hasName = (flags & 0x20) != 0
        self.hasRatio = (flags & 0x10) != 0
        self.hasColorTransform = (flags & 0x08) != 0
        self.hasMatrix = (flags & 0x04) != 0
        self.hasCharacter = (flags & 0x02) != 0
        self.hasMove = (flags & 0x01) != 0
        self.depth = data.readUI16()
        if self.hasCharacter:
            self.characterId = data.readUI16()
        if self.hasMatrix:
            self.matrix = data.readMATRIX()
        if self.hasColorTransform:
            self.colorTransform = data.readCXFORMWITHALPHA()
        if self.hasRatio:
            self.ratio = data.readUI16()
        if self.hasName:
            self.instanceName = data.readString()
        if self.hasClipDepth:
            self.clipDepth = data.readUI16()
        if self.hasClipActions:
            self.clipActions = data.readCLIPACTIONS(version);
            #raise Exception("PlaceObject2: ClipActions not yet implemented!")

    @property
    def name(self):
        return "PlaceObject2"

    @property
    def type(self):
        return TagPlaceObject2.TYPE

    @property
    def level(self):
        return 2

    @property
    def version(self):
        return 3

class TagRemoveObject2(TagRemoveObject):
    """
    The RemoveObject2 tag removes the character at the specified depth
    from the display list.
    The minimum file format version is SWF 3.
    """
    TYPE = 28

    def __init__(self):
        super(TagRemoveObject2, self).__init__()

    @property
    def name(self):
        return "RemoveObject2"

    @property
    def type(self):
        return TagRemoveObject2.TYPE

    @property
    def level(self):
        return 2

    @property
    def version(self):
        return 3

    def parse(self, data, length, version=1):
        self.depth = data.readUI16()

class TagDefineShape3(TagDefineShape2):
    """
    DefineShape3 extends the capabilities of DefineShape2 by extending
    all of the RGB color fields to support RGBA with opacity information.
    The minimum file format version is SWF 3.
    """
    TYPE = 32
    def __init__(self):
        super(TagDefineShape3, self).__init__()

    @property
    def name(self):
        return "DefineShape3"

    @property
    def type(self):
        return TagDefineShape3.TYPE

    @property
    def level(self):
        return 3

    @property
    def version(self):
        return 3

class TagDefineText2(TagDefineText):
    """
    The DefineText tag defines a block of static text. It describes the font,
    size, color, and exact position of every character in the text object.
    The minimum file format version is SWF 3.
    """
    TYPE = 33
    def __init__(self):
        super(TagDefineText2, self).__init__()

    @property
    def name(self):
        return "DefineText2"

    @property
    def type(self):
        return TagDefineText2.TYPE

    @property
    def level(self):
        return 2

    @property
    def version(self):
        return 3

class TagDefineBitsJPEG3(TagDefineBitsJPEG2):
    """
    This tag defines a bitmap character with JPEG compression. This tag
    extends DefineBitsJPEG2, adding alpha channel (opacity) data.
    Opacity/transparency information is not a standard feature in JPEG images,
    so the alpha channel information is encoded separately from the JPEG data,
    and compressed using the ZLIB standard for compression. The data format
    used by the ZLIB library is described by Request for Comments (RFCs)
    documents 1950 to 1952.
    The data in this tag begins with the JPEG SOI marker 0xFF, 0xD8 and ends
    with the EOI marker 0xFF, 0xD9. Before version 8 of the SWF file format,
    SWF files could contain an erroneous header of 0xFF, 0xD9, 0xFF, 0xD8
    before the JPEG SOI marker.
    In addition to specifying JPEG data, DefineBitsJPEG2 can also contain
    PNG image data and non-animated GIF89a image data.
    - If ImageData begins with the eight bytes 0x89 0x50 0x4E 0x47 0x0D 0x0A 0x1A 0x0A,
      the ImageData contains PNG data.
    - If ImageData begins with the six bytes 0x47 0x49 0x46 0x38 0x39 0x61,
      the ImageData contains GIF89a data.
    If ImageData contains PNG or GIF89a data, the optional BitmapAlphaData is
    not supported.
    The minimum file format version for this tag is SWF 3. The minimum file
    format version for embedding PNG of GIF89a data is SWF 8.
    """
    TYPE = 35
    def __init__(self):
        self.bitmapAlphaData = BytesIO()
        super(TagDefineBitsJPEG3, self).__init__()

    @property
    def name(self):
        return "DefineBitsJPEG3"

    @property
    def type(self):
        return TagDefineBitsJPEG3.TYPE

    @property
    def version(self):
        return 3 if self.bitmapType == BitmapType.JPEG else 8

    @property
    def level(self):
        return 3

    def parse(self, data, length, version=1):
        import zlib
        self.characterId = data.readUI16()
        alphaOffset = data.readUI32()
        self.bitmapAlphaData = BytesIO()
        self.bitmapData = BytesIO()
        self.bitmapData.write(data.f.read(alphaOffset))
        self.bitmapData.seek(0)
        self.bitmapType = ImageUtils.get_image_type(self.bitmapData)
        alphaDataSize = length - alphaOffset - 6
        if alphaDataSize > 0:
            self.bitmapAlphaData.write(data.f.read(alphaDataSize))
            self.bitmapAlphaData.seek(0)
            # decompress zlib encoded bytes
            zip = zlib.decompressobj()
            temp = BytesIO()
            temp.write(zip.decompress(self.bitmapAlphaData.read()))
            temp.seek(0)
            self.bitmapAlphaData = temp

class TagDefineBitsLossless2(TagDefineBitsLossless):
    """
    DefineBitsLossless2 extends DefineBitsLossless with support for
    opacity (alpha values). The colormap colors in colormapped images
    are defined using RGBA values, and direct images store 32-bit
    ARGB colors for each pixel. The intermediate 15-bit color depth
    is not available in DefineBitsLossless2.
    The minimum file format version for this tag is SWF 3.
    """
    TYPE = 36
    def __init__(self):
        super(TagDefineBitsLossless2, self).__init__()

    @property
    def name(self):
        return "DefineBitsLossless2"

    @property
    def type(self):
        return TagDefineBitsLossless2.TYPE

    @property
    def level(self):
        return 2

    @property
    def version(self):
        return 3

class TagDefineSprite(SWFTimelineContainer):
    """
    The DefineSprite tag defines a sprite character. It consists of
    a character ID and a frame count, followed by a series of control
    tags. The sprite is terminated with an End tag.
    The length specified in the Header reflects the length of the
    entire DefineSprite tag, including the ControlTags field.
    Definition tags (such as DefineShape) are not allowed in the
    DefineSprite tag. All of the characters that control tags refer to
    in the sprite must be defined in the main body of the file before
    the sprite is defined.
    The minimum file format version is SWF 3.
    """
    TYPE = 39
    frameCount = 0
    def __init__(self):
        super(TagDefineSprite, self).__init__()

    def parse(self, data, length, version=1):
        self.characterId = data.readUI16()
        self.frameCount = data.readUI16()
        self.parse_tags(data, version)

    def get_dependencies(self):
        s = super(TagDefineSprite, self).get_dependencies()
        s.add(self.characterId)
        return s

    @property
    def name(self):
        return "DefineSprite"

    @property
    def type(self):
        return TagDefineSprite.TYPE

    def __str__(self):
        s = super(TagDefineSprite, self).__str__() + " " + \
            "ID: %d" % self.characterId
        return s

class TagFrameLabel(Tag):
    """
    The FrameLabel tag gives the specified Name to the current frame.
    ActionGoToLabel uses this name to identify the frame.
    The minimum file format version is SWF 3.
    """
    TYPE = 43
    frameName = ""
    namedAnchorFlag = False
    def __init__(self):
        super(TagFrameLabel, self).__init__()

    @property
    def name(self):
        return "FrameLabel"

    @property
    def type(self):
        return TagFrameLabel.TYPE

    @property
    def level(self):
        return 1

    @property
    def version(self):
        return 3

    def parse(self, data, length, version=1):
        start = data.tell()
        self.frameName = data.readString()
        if (data.tell() - start) < length:
            data.readUI8() # Named anchor flag, always 1
            self.namedAnchorFlag = True

class TagDefineMorphShape(DefinitionTag):
    """
    The DefineMorphShape tag defines the start and end states of a morph
    sequence. A morph object should be displayed with the PlaceObject2 tag,
    where the ratio field specifies how far the morph has progressed.
    The minimum file format version is SWF 3.
    """
    TYPE = 46
    def __init__(self):
        self._morphFillStyles = []
        self._morphLineStyles = []
        super(TagDefineMorphShape, self).__init__()

    @property
    def name(self):
        return "DefineMorphShape"

    @property
    def type(self):
        return TagDefineMorphShape.TYPE

    @property
    def level(self):
        return 1

    @property
    def version(self):
        return 3

    @property
    def morph_fill_styles(self):
        """ Return list of SWFMorphFillStyle """
        return self._morphFillStyles

    @property
    def morph_line_styles(self):
        """ Return list of SWFMorphLineStyle """
        return self._morphLineStyles

    def parse(self, data, length, version=1):
        self._morphFillStyles = []
        self._morphLineStyles = []
        self.characterId = data.readUI16()
        self.startBounds = data.readRECT()
        self.endBounds = data.readRECT()
        offset = data.readUI32()

        self._morphFillStyles = data.readMORPHFILLSTYLEARRAY()
        self._morphLineStyles = data.readMORPHLINESTYLEARRAY(version = 1)
        self.startEdges = data.readSHAPE();
        self.endEdges = data.readSHAPE();

class TagDefineFont2(TagDefineFont):
    TYPE= 48
    def __init__(self):
        self.glyphShapeTable = []
        super(TagDefineFont2, self).__init__()

    @property
    def name(self):
        return "DefineFont2"

    @property
    def type(self):
        return TagDefineFont2.TYPE

    @property
    def level(self):
        return 2

    @property
    def version(self):
        return 3

    @property
    def unitDivisor(self):
        return 20

    def parse(self, data, length, version=1):
        self.glyphShapeTable = []
        self.codeTable = []
        self.fontAdvanceTable = []
        self.fontBoundsTable = []
        self.fontKerningTable = []

        self.characterId = data.readUI16()

        flags = data.readUI8()

        self.hasLayout = ((flags & 0x80) != 0)
        self.shiftJIS = ((flags & 0x40) != 0)
        self.smallText = ((flags & 0x20) != 0)
        self.ansi = ((flags & 0x10) != 0)
        self.wideOffsets = ((flags & 0x08) != 0)
        self.wideCodes = ((flags & 0x04) != 0)
        self.italic = ((flags & 0x02) != 0)
        self.bold = ((flags & 0x01) != 0)
        self.languageCode = data.readLANGCODE()

        fontNameLen = data.readUI8()
        fontNameRaw = BytesIO()
        fontNameRaw.write(data.f.read(fontNameLen))
        fontNameRaw.seek(0)
        self.fontName = fontNameRaw.read()

        numGlyphs = data.readUI16()
        numSkip = 2 if self.wideOffsets else 1
        # don't # Skip offsets. We don't need them.
        # Adobe Flash Player works in this way

        startOfOffsetTable = data.f.tell()
        offsetTable = []
        for i in range(0, numGlyphs):
            offsetTable.append(data.readUI32() if self.wideOffsets else data.readUI16())

        codeTableOffset = data.readUI32() if self.wideOffsets else data.readUI16()
        for i in range(0, numGlyphs):
            data.f.seek(startOfOffsetTable + offsetTable[i])
            self.glyphShapeTable.append(data.readSHAPE(self.unitDivisor))
        data.f.seek(startOfOffsetTable + codeTableOffset)
        for i in range(0, numGlyphs):
            self.codeTable.append(data.readUI16() if self.wideCodes else data.readUI8())

        if self.hasLayout:
            self.ascent = data.readSI16()
            self.descent = data.readSI16()
            self.leading = data.readSI16()
            for i in range(0, numGlyphs):
                self.fontAdvanceTable.append(data.readSI16())
            for i in range(0, numGlyphs):
                self.fontBoundsTable.append(data.readRECT())
            kerningCount = data.readUI16()
            for i in range(0, kerningCount):
                self.fontKerningTable.append(data.readKERNINGRECORD(self.wideCodes))

class TagFileAttributes(Tag):
    """
    The FileAttributes tag defines characteristics of the SWF file. This tag
    is required for SWF 8 and later and must be the first tag in the SWF file.
    Additionally, the FileAttributes tag can optionally be included in all SWF
    file versions.
    The HasMetadata flag identifies whether the SWF file contains the Metadata
    tag. Flash Player does not care about this bit field or the related tag but
    it is useful for search engines.
    The UseNetwork flag signifies whether Flash Player should grant the SWF file
    local or network file access if the SWF file is loaded locally. The default
    behavior is to allow local SWF files to interact with local files only, and
    not with the network. However, by setting the UseNetwork flag, the local SWF
    can forfeit its local file system access in exchange for access to the
    network. Any version of SWF can use the UseNetwork flag to set the file
    access for locally loaded SWF files that are running in Flash Player 8 or later.
    """
    TYPE = 69
    def __init__(self):
        super(TagFileAttributes, self).__init__()

    @property
    def name(self):
        return "FileAttributes"

    @property
    def type(self):
        return TagFileAttributes.TYPE

    @property
    def level(self):
        return 1

    @property
    def version(self):
        return 8

    def parse(self, data, length, version=1):
        flags = data.readUI8()
        self.useDirectBlit = ((flags & 0x40) != 0)
        self.useGPU = ((flags & 0x20) != 0)
        self.hasMetadata = ((flags & 0x10) != 0)
        self.actionscript3 = ((flags & 0x08) != 0)
        self.useNetwork = ((flags & 0x01) != 0)
        data.skip_bytes(3)

    def __str__(self):
        s = super(TagFileAttributes, self).__str__() + \
            " useDirectBlit: %d, " % self.useDirectBlit + \
            "useGPU: %d, " % self.useGPU + \
            "hasMetadata: %d, " % self.hasMetadata + \
            "actionscript3: %d, " % self.actionscript3 + \
            "useNetwork: %d" % self.useNetwork
        return s

class TagPlaceObject3(TagPlaceObject2):
    TYPE = 70
    def __init__(self):
        super(TagPlaceObject3, self).__init__()

    def parse(self, data, length, version=1):
        flags = data.readUI8()
        self.hasClipActions = ((flags & 0x80) != 0)
        self.hasClipDepth = ((flags & 0x40) != 0)
        self.hasName = ((flags & 0x20) != 0)
        self.hasRatio = ((flags & 0x10) != 0)
        self.hasColorTransform = ((flags & 0x08) != 0)
        self.hasMatrix = ((flags & 0x04) != 0)
        self.hasCharacter = ((flags & 0x02) != 0)
        self.hasMove = ((flags & 0x01) != 0)
        flags2 = data.readUI8();
        self.hasImage = ((flags2 & 0x10) != 0)
        self.hasClassName = ((flags2 & 0x08) != 0)
        self.hasCacheAsBitmap = ((flags2 & 0x04) != 0)
        self.hasBlendMode = ((flags2 & 0x2) != 0)
        self.hasFilterList = ((flags2 & 0x1) != 0)
        self.depth = data.readUI16()

        if self.hasClassName:
            self.className = data.readString()
        if self.hasCharacter:
            self.characterId = data.readUI16()
        if self.hasMatrix:
            self.matrix = data.readMATRIX()
        if self.hasColorTransform:
            self.colorTransform = data.readCXFORMWITHALPHA()
        if self.hasRatio:
            self.ratio = data.readUI16()
        if self.hasName:
            self.instanceName = data.readString()
        if self.hasClipDepth:
            self.clipDepth = data.readUI16();
        if self.hasFilterList:
            numberOfFilters = data.readUI8()
            for i in range(0, numberOfFilters):
                self._surfaceFilterList.append(data.readFILTER())
        if self.hasBlendMode:
            self.blendMode = data.readUI8()
        if self.hasCacheAsBitmap:
            self.bitmapCache = data.readUI8()
        if self.hasClipActions:
            self.clipActions = data.readCLIPACTIONS(version)
            #raise Exception("PlaceObject3: ClipActions not yet implemented!")

    @property
    def name(self):
        return "PlaceObject3"

    @property
    def type(self):
        return TagPlaceObject3.TYPE

class TagDoABCDefine(Tag):
    TYPE = 72
    def __init__(self):
        super(TagDoABCDefine, self).__init__()

    @property
    def name(self):
        return "DoABCDefine"

    @property
    def type(self):
        return TagDoABCDefine.TYPE

    @property
    def level(self):
        return 1

    @property
    def version(self):
        return 9

    def parse(self, data, length, version=1):
        pos = data.tell()
        self.bytes = data.f.read(length - (data.tell() - pos))

class TagDefineFontAlignZones(Tag):
    TYPE = 73
    def __init__(self):
        super(TagDefineFontAlignZones, self).__init__()

    @property
    def name(self):
        return "DefineFontAlignZones"

    @property
    def type(self):
        return TagDefineFontAlignZones.TYPE

    @property
    def level(self):
        return 1

    @property
    def version(self):
        return 8

    def parse(self, data, length, version=1):
        self.zoneTable = []

        self.fontId = data.readUI16()
        self.csmTableHint = (data.readUI8() >> 6)

        recordsEndPos = data.tell() + length - 3;
        while data.tell() < recordsEndPos:
            self.zoneTable.append(data.readZONERECORD())

class TagCSMTextSettings(Tag):
    TYPE = 74
    def __init__(self):
        super(TagCSMTextSettings, self).__init__()

    @property
    def name(self):
        return "CSMTextSettings"

    @property
    def type(self):
        return TagCSMTextSettings.TYPE

    @property
    def level(self):
        return 1

    @property
    def version(self):
        return 8

    def parse(self, data, length, version=1):
        self.textId = data.readUI16()
        self.useFlashType = data.readUB(2)
        self.gridFit = data.readUB(3);
        data.readUB(3) # reserved, always 0
        self.thickness = data.readFIXED()
        self.sharpness = data.readFIXED()
        data.readUI8() # reserved, always 0

class TagDefineFont3(TagDefineFont2):
    TYPE = 75
    def __init__(self):
        super(TagDefineFont3, self).__init__()

    @property
    def name(self):
        return "DefineFont3"

    @property
    def type(self):
        return TagDefineFont3.TYPE

    @property
    def level(self):
        return 2

    @property
    def version(self):
        return 8

class TagSymbolClass(Tag):
    TYPE = 76
    def __init__(self):
        self.symbols = []
        super(TagSymbolClass, self).__init__()

    @property
    def name(self):
        return "SymbolClass"

    @property
    def type(self):
        return TagSymbolClass.TYPE

    @property
    def level(self):
        return 1

    @property
    def version(self):
        return 9 # educated guess (not specified in SWF10 spec)

    def parse(self, data, length, version=1):
        self.symbols = []
        numSymbols = data.readUI16()
        for i in range(0, numSymbols):
            self.symbols.append(data.readSYMBOL())

class TagMetadata(Tag):
    TYPE = 77
    def __init__(self):
        super(TagMetadata, self).__init__()

    @property
    def name(self):
        return "Metadata"

    @property
    def type(self):
        return TagMetadata.TYPE

    @property
    def level(self):
        return 1

    @property
    def version(self):
        return 1

    def parse(self, data, length, version=1):
        self.xmlString = data.readString()

    def __str__(self):
        s = super(TagMetadata, self).__str__()
        s += " xml: %r" % self.xmlString
        return s

class TagDoABC(Tag):
    TYPE = 82
    def __init__(self):
        super(TagDoABC, self).__init__()

    @property
    def name(self):
        return "DoABC"

    @property
    def type(self):
        return TagDoABC.TYPE

    @property
    def level(self):
        return 1

    @property
    def version(self):
        return 9

    def parse(self, data, length, version=1):
        pos = data.tell()
        flags = data.readUI32()
        self.lazyInitializeFlag = ((flags & 0x01) != 0)
        self.abcName = data.readString()
        self.bytes = data.f.read(length - (data.tell() - pos))

class TagDefineShape4(TagDefineShape3):
    TYPE = 83
    def __init__(self):
        super(TagDefineShape4, self).__init__()

    @property
    def name(self):
        return "DefineShape4"

    @property
    def type(self):
        return TagDefineShape4.TYPE

    @property
    def level(self):
        return 4

    @property
    def version(self):
        return 8

    def parse(self, data, length, version=1):
        self.characterId = data.readUI16()
        self._shape_bounds = data.readRECT()
        self.edge_bounds = data.readRECT()
        flags = data.readUI8()
        self.uses_fillwinding_rule = ((flags & 0x04) != 0)
        self.uses_non_scaling_strokes = ((flags & 0x02) != 0)
        self.uses_scaling_strokes = ((flags & 0x01) != 0)
        self._shapes = data.readSHAPEWITHSTYLE(self.level)

class TagDefineSceneAndFrameLabelData(Tag):
    TYPE = 86
    def __init__(self):
        self.scenes = []
        self.frameLabels = []
        super(TagDefineSceneAndFrameLabelData, self).__init__()

    @property
    def name(self):
        return "DefineSceneAndFrameLabelData"

    @property
    def type(self):
        return TagDefineSceneAndFrameLabelData.TYPE

    @property
    def level(self):
        return 1

    @property
    def version(self):
        return 9

    def parse(self, data, length, version=1):
        self.sceneCount = data.readEncodedU32()

        if self.sceneCount >= 0x80000000:
            #print "WARNING: Negative sceneCount value: %x found!. SWF file exploiting CVE-2007-0071?" % self.sceneCount
            return

        self.scenes = []
        self.frameLabels = []
        for i in range(0, self.sceneCount):
            sceneOffset = data.readEncodedU32()
            sceneName = data.readString()
            self.scenes.append(SWFScene(sceneOffset, sceneName))

        frameLabelCount = data.readEncodedU32()
        for i in range(0, frameLabelCount):
            frameNumber = data.readEncodedU32();
            frameLabel = data.readString();
            self.frameLabels.append(SWFFrameLabel(frameNumber, frameLabel))

class TagDefineBinaryData(DefinitionTag):
    """
	The DefineBinaryData tag permits arbitrary binary data to be embedded in a SWF file. DefineBinaryData is a definition tag, like DefineShape and DefineSprite. It associates a blob of binary data with a standard SWF 16-bit character ID. The character ID is entered into the SWF file's character dictionary. DefineBinaryData is intended to be used in conjunction with the SymbolClass tag. The SymbolClass tag can be used to associate a DefineBinaryData tag with an AS3 class definition. The AS3 class must be a subclass of ByteArray. When the class is instantiated, it will be populated automatically with the contents of the binary data resource.
    """
    TYPE = 87
    def __init__(self):
        super(TagDefineBinaryData, self).__init__()

    @property
    def name(self):
        return "DefineBinaryData"

    @property
    def type(self):
        return TagDefineBinaryData.TYPE

    def parse(self, data, length, version=1):
        self.characterId = data.readUI16()
        self.reserved = data.readUI32()
        self.data = data.read(length - 6)

class TagDefineFontName(Tag):
    TYPE = 88
    def __init__(self):
        super(TagDefineFontName, self).__init__()

    @property
    def name(self):
        return "DefineFontName"

    @property
    def type(self):
        return TagDefineFontName.TYPE

    @property
    def level(self):
        return 1

    @property
    def version(self):
        return 9

    def get_dependencies(self):
        s = super(TagDefineFontName, self).get_dependencies()
        s.add(self.fontId)
        return s

    def parse(self, data, length, version=1):
        self.fontId = data.readUI16()
        self.fontName = data.readString()
        self.fontCopyright = data.readString()

class TagDefineSound(Tag):
    TYPE = 14
    def __init__(self):
        super(TagDefineSound, self).__init__()

    @property
    def name(self):
        return "TagDefineSound"

    @property
    def type(self):
        return TagDefineSound.TYPE

    @property
    def level(self):
        return 1

    @property
    def version(self):
        return 1

    def parse(self, data, length, version=1):
        assert length > 7
        self.soundId = data.readUI16()
        self.soundFormat = data.readUB(4)
        self.soundRate = data.readUB(2)
        self.soundSampleSize = data.readUB(1)
        self.soundChannels = data.readUB(1)
        self.soundSamples = data.readUI32()
        # used 2 + 1 + 4 bytes here
        self.soundData = BytesIO(data.read(length - 7))

    def __str__(self):
        s = super(TagDefineSound, self).__str__()
        s += " soundFormat: %s" % AudioCodec.tostring(self.soundFormat)
        s += " soundRate: %s" % AudioSampleRate.tostring(self.soundRate)
        s += " soundSampleSize: %s" % AudioSampleSize.tostring(self.soundSampleSize)
        s += " soundChannels: %s" % AudioChannels.tostring(self.soundChannels)
        return s

class TagStartSound(Tag):
    TYPE = 15
    def __init__(self):
        super(TagStartSound, self).__init__()

    @property
    def name(self):
        return "TagStartSound"

    @property
    def type(self):
        return TagStartSound.TYPE

    @property
    def level(self):
        return 1

    @property
    def version(self):
        return 1

    def parse(self, data, length, version=1):
        self.soundId = data.readUI16()
        self.soundInfo = data.readSOUNDINFO()

class TagStartSound2(Tag):
    TYPE = 89
    def __init__(self):
        super(TagStartSound2, self).__init__()

    @property
    def name(self):
        return "TagStartSound2"

    @property
    def type(self):
        return TagStartSound2.TYPE

    @property
    def level(self):
        return 1

    @property
    def version(self):
        return 9

    def parse(self, data, length, version=1):
        self.soundClassName = data.readString()
        self.soundInfo = data.readSOUNDINFO()

class TagSoundStreamHead(Tag):
    TYPE = 18
    def __init__(self):
        super(TagSoundStreamHead, self).__init__()

    @property
    def name(self):
        return "TagSoundStreamHead"

    @property
    def type(self):
        return TagSoundStreamHead.TYPE

    @property
    def level(self):
        return 1

    @property
    def version(self):
        return 1

    def parse(self, data, length, version=1):
        # byte 1
        self.reserved0 = data.readUB(4)
        self.playbackRate = data.readUB(2)
        self.playbackSampleSize = data.readUB(1)
        self.playbackChannels = data.readUB(1)

        # byte 2
        self.soundFormat = data.readUB(4)
        self.soundRate = data.readUB(2)
        self.soundSampleSize = data.readUB(1)
        self.soundChannels = data.readUB(1)

        self.samples = data.readUI16()
        self.latencySeek = data.readSI16() if self.soundFormat == AudioCodec.MP3 else None
        hdr = 6 if self.soundFormat == AudioCodec.MP3 else 4
        assert hdr == length

    def __str__(self):
        s = super(TagSoundStreamHead, self).__str__()
        s += " playbackRate: %s" % AudioSampleRate.tostring(self.playbackRate)
        s += " playbackSampleSize: %s" % AudioSampleSize.tostring(self.playbackSampleSize)
        s += " playbackChannels: %s" % AudioChannels.tostring(self.playbackChannels)
        s += " soundFormat: %s" % AudioCodec.tostring(self.soundFormat)
        s += " soundRate: %s" % AudioSampleRate.tostring(self.soundRate)
        s += " soundSampleSize: %s" % AudioSampleSize.tostring(self.soundSampleSize)
        s += " soundChannels: %s" % AudioChannels.tostring(self.soundChannels)
        return s

class TagSoundStreamHead2(TagSoundStreamHead):
    """
    The SoundStreamHead2 tag is identical to the SoundStreamHead tag, except it allows
    different values for StreamSoundCompression and StreamSoundSize (SWF 3 file format).
    """
    TYPE = 45

    def __init__(self):
        super(TagSoundStreamHead2, self).__init__()

    @property
    def name(self):
        return "TagSoundStreamHead2"

    @property
    def type(self):
        return TagSoundStreamHead2.TYPE

class TagSoundStreamBlock(Tag):
    """
    The SoundStreamHead2 tag is identical to the SoundStreamHead tag, except it allows
    different values for StreamSoundCompression and StreamSoundSize (SWF 3 file format).
    """
    TYPE = 19

    def __init__(self):
        super(TagSoundStreamBlock, self).__init__()

    @property
    def name(self):
        return "TagSoundStreamBlock"

    @property
    def type(self):
        return TagSoundStreamBlock.TYPE

    def parse(self, data, length, version=1):
        # unfortunately we can't see our associated SoundStreamHead from here,
        # so just stash the data
        self.data = BytesIO(data.read(length))

    def complete_parse_with_header(self, head):
        stream = SWFStream(self.data)
        if head.soundFormat in (AudioCodec.UncompressedNativeEndian,
                                AudioCodec.UncompressedLittleEndian):
            pass # data is enough
        elif head.soundFormat == AudioCodec.MP3:
            self.sampleCount = stream.readUI16()
            self.seekSize = stream.readSI16()
            self.mpegFrames = stream.read()

class TagDefineBinaryData(DefinitionTag):
    """
    The DefineBinaryData tag permits arbitrary binary data to be embedded in a SWF file.
    DefineBinaryData is a definition tag, like DefineShape and DefineSprite. It associates a blob
    of binary data with a standard SWF 16-bit character ID. The character ID is entered into the
    SWF file's character dictionary.
    """
    TYPE = 87

    def __init__(self):
        super(TagDefineBinaryData, self).__init__()

    @property
    def name(self):
        return "TagDefineBinaryData"

    @property
    def type(self):
        return TagDefineBinaryData.TYPE

    def parse(self, data, length, version=1):
        assert length >= 6
        self.characterId = data.readUI16()
        self.reserved = data.readUI32()
        self.data = data.read(length - 4 - 2)

class TagProductInfo(Tag):
    """
    Undocumented in SWF10.
    """
    TYPE = 41

    def __init__(self):
        super(TagProductInfo, self).__init__()

    @property
    def name(self):
        return "TagProductInfo"

    @property
    def type(self):
        return TagProductInfo.TYPE

    def parse(self, data, length, version=1):
        self.product = data.readUI32()
        self.edition = data.readUI32()
        self.majorVersion, self.minorVersion = data.readUI8(), data.readUI8()
        self.build = data.readUI64()
        self.compileTime = data.readUI64()

    def __str__(self):
        s = super(TagProductInfo, self).__str__()
        s += " product: %s" % ProductKind.tostring(self.product)
        s += " edition: %s" % ProductEdition.tostring(self.edition)
        s += " major.minor.build: %d.%d.%d" % (self.majorVersion, self.minorVersion, self.build)
        s += " compileTime: %d (%s)" % (self.compileTime, datetime.datetime.fromtimestamp(self.compileTime//1000.0).ctime())
        return s

class TagScriptLimits(Tag):
    """
    The ScriptLimits tag includes two fields that can be used to override the default settings for
    maximum recursion depth and ActionScript time-out: MaxRecursionDepth and
    ScriptTimeoutSeconds.
    """
    TYPE = 65

    def __init__(self):
        super(TagScriptLimits, self).__init__()

    @property
    def name(self):
        return "TagScriptLimits"

    @property
    def type(self):
        return TagScriptLimits.TYPE

    def parse(self, data, length, version=1):
        self.maxRecursionDepth = data.readUI16()
        self.scriptTimeoutSeconds = data.readUI16()

    def __str__(self):
        s = super(TagScriptLimits, self).__str__()
        s += " maxRecursionDepth: %s" % self.maxRecursionDepth
        s += " scriptTimeoutSeconds: %s" % self.scriptTimeoutSeconds
        return s

class TagDebugID(Tag):
    """
    Undocumented in SWF10.  Some kind of GUID.
    """
    TYPE = 63

    def __init__(self):
        super(TagDebugID, self).__init__()

    @property
    def name(self):
        return "TagDebugID"

    @property
    def type(self):
        return TagDebugID.TYPE

    def parse(self, data, length, version=1):
        self.guid = data.read(16)

class TagExportAssets(Tag):
    """
    The ExportAssets tag makes portions of a SWF file available for import by other SWF files
    """
    TYPE = 56

    def __init__(self):
        super(TagExportAssets, self).__init__()

    @property
    def name(self):
        return "TagExportAssets"

    @property
    def version(self):
        return 5

    @property
    def type(self):
        return TagExportAssets.TYPE

    def parse(self, data, length, version=1):
        self.count = data.readUI16()
        self.exports = [data.readEXPORT() for i in range(self.count)]

    def __str__(self):
        s = super(TagExportAssets, self).__str__()
        s += " exports: %s" % self.exports
        return s

class TagProtect(Tag):
    """
    The Protect tag marks a file as not importable for editing in an authoring environment. If the
    Protect tag contains no data (tag length = 0), the SWF file cannot be imported. If this tag is
    present in the file, any authoring tool should prevent the file from loading for editing.
    """
    TYPE = 24

    def __init__(self):
        super(TagProtect, self).__init__()
        self.password = None

    @property
    def name(self):
        return "TagProtect"

    @property
    def version(self):
        return 2 if self.password is None else 5

    @property
    def type(self):
        return TagProtect.TYPE

    def parse(self, data, length, version=1):
        if length:
            self.password = data.readString()
        else:
            self.password = None

    def __str__(self):
        s = super(TagProtect, self).__str__()
        s += " password: %r" % self.password
        return s

class TagEnableDebugger(Tag):
    """
    The EnableDebugger tag enables debugging. The password in the EnableDebugger tag is
    encrypted by using the MD5 algorithm, in the same way as the Protect tag.
    """
    TYPE = 58

    def __init__(self):
        super(TagEnableDebugger, self).__init__()

    @property
    def name(self):
        return "TagEnableDebugger"

    @property
    def version(self):
        return 5

    @property
    def type(self):
        return TagEnableDebugger.TYPE

    def parse(self, data, length, version=1):
        self.password = data.readString()

    def __str__(self):
        s = super(TagEnableDebugger, self).__str__()
        s += " password: %r" % self.password
        return s

class TagEnableDebugger2(Tag):
    """
    The EnableDebugger2 tag enables debugging. The Password field is encrypted by using the
    MD5 algorithm, in the same way as the Protect tag.
    """
    TYPE = 64

    def __init__(self):
        super(TagEnableDebugger2, self).__init__()

    @property
    def name(self):
        return "TagEnableDebugger2"

    @property
    def version(self):
        return 6

    @property
    def type(self):
        return TagEnableDebugger2.TYPE

    def parse(self, data, length, version=1):
        self.reserved0 = data.readUI16()
        self.password = data.readString()

    def __str__(self):
        s = super(TagEnableDebugger2, self).__str__()
        s += " password: %r" % self.password
        return s

class TagDoInitAction(Tag):
    """
    The DoInitAction tag is similar to the DoAction tag: it defines a series of bytecodes to be
    executed. However, the actions defined with DoInitAction are executed earlier than the usual
    DoAction actions, and are executed only once.
    """
    TYPE = 59

    def __init__(self):
        super(TagDoInitAction, self).__init__()

    @property
    def name(self):
        return "TagDoInitAction"

    @property
    def version(self):
        return 6

    @property
    def type(self):
        return TagDoInitAction.TYPE

    def get_dependencies(self):
        s = super(TagDoInitAction, self).get_dependencies()
        s.add(self.spriteId)
        return s

    def parse(self, data, length, version=1):
        self.spriteId = data.readUI16()
        self.actions = data.readACTIONRECORDs()

class TagDefineEditText(DefinitionTag):
    """
    The DefineEditText tag defines a dynamic text object, or text field.

    A text field is associated with an ActionScript variable name where the contents of the text
    field are stored. The SWF file can read and write the contents of the variable, which is always
    kept in sync with the text being displayed. If the ReadOnly flag is not set, users may change
    the value of a text field interactively
    """
    TYPE = 37

    def __init__(self):
        super(TagDefineEditText, self).__init__()

    @property
    def name(self):
        return "TagDefineEditText"

    @property
    def type(self):
        return TagDefineEditText.TYPE

    def get_dependencies(self):
        s = super(TagDefineEditText, self).get_dependencies()
        s.add(self.fontId) if self.hasFont else None
        return s

    def parse(self, data, length, version=1):
        self.characterId = data.readUI16()
        self.bounds = data.readRECT()

        # flags
        self.hasText = data.readUB(1) == 1
        self.wordWrap = data.readUB(1) == 1
        self.multiline = data.readUB(1) == 1
        self.password = data.readUB(1) == 1

        self.readOnly = data.readUB(1) == 1
        self.hasTextColor = data.readUB(1) == 1
        self.hasMaxLength = data.readUB(1) == 1
        self.hasFont = data.readUB(1) == 1

        self.hasFontClass = data.readUB(1) == 1
        self.autoSize = data.readUB(1) == 1
        self.hasLayout = data.readUB(1) == 1
        self.noSelect = data.readUB(1) == 1

        self.border = data.readUB(1) == 1
        self.wasStatic = data.readUB(1) == 1
        self.html = data.readUB(1) == 1
        self.useOutlines = data.readUB(1) == 1

        # values
        self.fontId = data.readUI16() if self.hasFont else None
        self.fontClass = data.readString() if self.hasFontClass else None
        self.fontHeight = data.readUI16() if self.hasFont else None
        self.textColor = data.readRGBA() if self.hasTextColor else None
        self.maxLength = data.readUI16() if self.hasMaxLength else None

        self.align = data.readUI8() if self.hasLayout else None
        self.leftMargin = data.readUI16() if self.hasLayout else None
        self.rightMargin = data.readUI16() if self.hasLayout else None
        self.indent = data.readUI16() if self.hasLayout else None
        self.leading = data.readUI16() if self.hasLayout else None

        # backend info
        self.variableName = data.readString()
        self.initialText = data.readString() if self.hasText else None

class TagDefineButton(DefinitionTag):
    """
    The DefineButton tag defines a button character for later use by control tags such as
    PlaceObject.
    """
    TYPE = 7

    def __init__(self):
        super(TagDefineButton, self).__init__()

    @property
    def name(self):
        return "TagDefineButton"

    @property
    def type(self):
        return TagDefineButton.TYPE

    def get_dependencies(self):
        s = super(TagDefineButton, self).get_dependencies()
        for b in self.buttonCharacters:
            s.update(b.get_dependencies())
        return s

    def parse(self, data, length, version=1):
        self.characterId = data.readUI16()
        self.buttonCharacters = data.readBUTTONRECORDs(version = 1)
        self.buttonActions = data.readACTIONRECORDs()

class TagDefineButton2(DefinitionTag):
    """
    DefineButton2 extends the capabilities of DefineButton by allowing any state transition to
    trigger actions.
    """
    TYPE = 34

    def __init__(self):
        super(TagDefineButton2, self).__init__()

    @property
    def name(self):
        return "TagDefineButton2"

    @property
    def type(self):
        return TagDefineButton2.TYPE

    def get_dependencies(self):
        s = super(TagDefineButton2, self).get_dependencies()
        for b in self.buttonCharacters:
            s.update(b.get_dependencies())
        return s

    def parse(self, data, length, version=1):
        self.characterId = data.readUI16()
        self.reservedFlags = data.readUB(7)
        self.trackAsMenu = data.readUB(1) == 1
        offs = data.tell()
        self.actionOffset = data.readUI16()
        self.buttonCharacters = data.readBUTTONRECORDs(version = 2)

        if self.actionOffset:
            # if we have actions, seek to the first one
            data.seek(offs + self.actionOffset)
            self.buttonActions = data.readBUTTONCONDACTIONSs()

class TagDefineButtonSound(Tag):
    """
    The DefineButtonSound tag defines which sounds (if any) are played on state transitions.
    """
    TYPE = 17

    def __init__(self):
        super(TagDefineButtonSound, self).__init__()

    @property
    def name(self):
        return "TagDefineButtonSound"

    @property
    def type(self):
        return TagDefineButtonSound.TYPE

    @property
    def version(self):
        return 2

    def parse(self, data, length, version=1):
        self.buttonId = data.readUI16()

        for event in 'OverUpToIdle IdleToOverUp OverUpToOverDown OverDownToOverUp'.split():
            soundId = data.readUI16()
            setattr(self, 'soundOn' + event, soundId)
            soundInfo = data.readSOUNDINFO() if soundId else None
            setattr(self, 'soundInfoOn' + event, soundInfo)

class TagDefineScalingGrid(Tag):
    """
    The DefineScalingGrid tag introduces the concept of 9-slice scaling, which allows
    component-style scaling to be applied to a sprite or button character.
    """
    TYPE = 78

    def __init__(self):
        super(TagDefineScalingGrid, self).__init__()

    @property
    def name(self):
        return "TagDefineScalingGrid"

    @property
    def type(self):
        return TagDefineScalingGrid.TYPE

    def parse(self, data, length, version=1):
        self.characterId = data.readUI16()
        self.splitter = data.readRECT()

class TagDefineVideoStream(DefinitionTag):
    """
    DefineVideoStream defines a video character that can later be placed on the display list.
    """
    TYPE = 60

    def __init__(self):
        super(TagDefineVideoStream, self).__init__()

    @property
    def name(self):
        return "TagDefineVideoStream"

    @property
    def type(self):
        return TagDefineVideoStream.TYPE

    def parse(self, data, length, version=1):
        self.characterId = data.readUI16()
        self.numFrames = data.readUI16()
        self.width = data.readUI16()
        self.height = data.readUI16()
        reserved0 = data.readUB(4)
        self.videoDeblocking = data.readUB(3)
        self.videoSmoothing = data.readUB(1)
        self.codec = data.readUI8()

class TagVideoFrame(Tag):
    """
    VideoFrame provides a single frame of video data for a video character that is already defined
    with DefineVideoStream.
    """
    TYPE = 61

    def __init__(self):
        super(TagVideoFrame, self).__init__()

    @property
    def name(self):
        return "TagVideoFrame"

    @property
    def type(self):
        return TagVideoFrame.TYPE

    def parse(self, data, length, version=1):
        self.streamId = data.readUI16()
        self.frameNumber = data.readUI16()
        self.videoData = data.read(length - 4)

class TagDefineMorphShape2(TagDefineMorphShape):
    """
    The DefineMorphShape2 tag extends the capabilities of DefineMorphShape by using a new
    morph line style record in the morph shape. MORPHLINESTYLE2 allows the use of new
    types of joins and caps as well as scaling options and the ability to fill the strokes of the morph
    shape.
    """
    TYPE = 84

    @property
    def name(self):
        return "TagDefineMorphShape2"

    @property
    def type(self):
        return TagDefineMorphShape2.TYPE

    @property
    def version(self):
        return 8

    def get_dependencies(self):
        s = super(TagDefineMorphShape2, self).get_dependencies()
        s.update(self.startEdges.get_dependencies())
        s.update(self.endEdges.get_dependencies())
        return s

    def parse(self, data, length, version=1):
        self._morphFillStyles = []
        self._morphLineStyles = []
        self.characterId = data.readUI16()

        self.startBounds = data.readRECT()
        self.endBounds = data.readRECT()
        self.startEdgeBounds = data.readRECT()
        self.endEdgeBounds = data.readRECT()

        self.reserved0 = data.readUB(6)
        self.usesNonScalingStrokes = data.readUB(1) == 1
        self.usesScalingStrokes = data.readUB(1) == 1

        offset = data.readUI32()
        self._morphFillStyles = data.readMORPHFILLSTYLEARRAY()
        self._morphLineStyles = data.readMORPHLINESTYLEARRAY(version = 2)

        self.startEdges = data.readSHAPE();
        self.endEdges = data.readSHAPE();

if __name__ == '__main__':
    # some table checks
    for x in range(256):
        y = TagFactory.create(x)
        if y:
            assert y.type == x, y.name + ' is misnamed'

    for k, v in globals().items():
        if k.startswith('Tag') and hasattr(v, 'TYPE'):
            y = TagFactory.create(v.TYPE)
            if y == None:
                #print v.__name__, 'missing', 'for', v.TYPE
                pass
