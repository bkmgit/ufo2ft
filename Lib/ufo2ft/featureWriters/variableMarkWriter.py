from ufo2ft.featureWriters import MarkFeatureWriter
from types import SimpleNamespace
from fontTools.feaLib.variableScalar import VariableScalar
from fontTools.feaLib import ast
from collections import OrderedDict, defaultdict
from ufo2ft.util import get_userspace_location, collapse_varscalar


class VariableMarkFeatureWriter(MarkFeatureWriter):
    def setContext(self, *args, **kwargs):
        # Rename "font" to "designspace" to avoid confusion
        super(MarkFeatureWriter, self).setContext(*args, **kwargs)
        self.context = SimpleNamespace(
            designspace=self.context.font,
            feaFile=self.context.feaFile,
            compiler=self.context.compiler,
            todo=self.context.todo,
            insertComments=self.context.insertComments,
            font=self.context.font.findDefault().font,
        )
        self.context.gdefClasses = self.getGDEFGlyphClasses()
        self.context.anchorLists = self._getAnchorLists()
        self.context.anchorPairs = self._getAnchorPairs()

        return self.context

    def _getAnchor(self, glyphName, anchorName):
        x_value = VariableScalar()
        y_value = VariableScalar()
        for source in self.context.designspace.sources:
            glyph = source.font[glyphName]
            for anchor in glyph.anchors:
                if anchor.name == anchorName:
                    location = get_userspace_location(
                        self.context.designspace, source.location
                    )
                    x_value.add_value(location, anchor.x)
                    y_value.add_value(location, anchor.y)
        return collapse_varscalar(x_value), collapse_varscalar(y_value)

    def _getAnchorLists(self):
        gdefClasses = self.context.gdefClasses
        if gdefClasses.base is not None:
            # only include the glyphs listed in the GDEF.GlyphClassDef groups
            include = gdefClasses.base | gdefClasses.ligature | gdefClasses.mark
        else:
            # no GDEF table defined in feature file, include all glyphs
            include = None
        result = OrderedDict()
        for glyphName, glyph in self.getOrderedGlyphSet().items():
            if include is not None and glyphName not in include:
                continue
            anchorDict = OrderedDict()
            for anchor in glyph.anchors:
                anchorName = anchor.name
                if not anchorName:
                    self.log.warning(
                        "unnamed anchor discarded in glyph '%s'", glyphName
                    )
                    continue
                if anchorName in anchorDict:
                    self.log.warning(
                        "duplicate anchor '%s' in glyph '%s'", anchorName, glyphName
                    )
                x, y = self._getAnchor(glyphName, anchorName)
                a = self.NamedAnchor(name=anchorName, x=x, y=y)
                anchorDict[anchorName] = a
            if anchorDict:
                result[glyphName] = list(anchorDict.values())
        return result
