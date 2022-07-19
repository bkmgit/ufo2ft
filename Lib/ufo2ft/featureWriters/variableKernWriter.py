from ufo2ft.featureWriters import KernFeatureWriter
from ufo2ft.featureWriters.kernFeatureWriter import (
    SIDE1_PREFIX,
    SIDE2_PREFIX,
    KerningPair,
)
from ufo2ft.util import get_userspace_location, collapse_varscalar
from fontTools.feaLib.variableScalar import VariableScalar
import logging

log = logging.getLogger(__file__)


class VariableKernFeatureWriter(KernFeatureWriter):
    @staticmethod
    def getKerningGroups(designspace, glyphSet=None):
        if glyphSet:
            allGlyphs = set(glyphSet.keys())
        else:
            allGlyphs = set(designspace.findDefault().font.keys())
        side1Groups = {}
        side2Groups = {}
        for source in designspace.sources:
            font = source.font
            for name, members in font.groups.items():
                # prune non-existent or skipped glyphs
                members = [g for g in members if g in allGlyphs]
                if not members:
                    # skip empty groups
                    continue
                # skip groups without UFO3 public.kern{1,2} prefix
                if name.startswith(SIDE1_PREFIX):
                    if name in side1Groups and side1Groups[name] != members:
                        log.warning(
                            "incompatible left groups: %s was previously %s, %s tried to make it %s",
                            name,
                            side1Groups[name],
                            font,
                            members,
                        )
                        continue
                    side1Groups[name] = members
                elif name.startswith(SIDE2_PREFIX):
                    if name in side2Groups and side2Groups[name] != members:
                        log.warning(
                            "incompatible right groups: %s was previously %s, %s tried to make it %s",
                            name,
                            side2Groups[name],
                            font,
                            members,
                        )
                        continue
                    side2Groups[name] = members
        return side1Groups, side2Groups

    @staticmethod
    def getKerningPairs(designspace, side1Classes, side2Classes, glyphSet=None):
        default_font = designspace.findDefault().font
        if glyphSet:
            allGlyphs = set(glyphSet.keys())
        else:
            allGlyphs = set(default_font)

        pairsByFlags = {}
        for source in designspace.sources:
            for (side1, side2) in source.font.kerning:
                # filter out pairs that reference missing groups or glyphs
                if side1 not in side1Classes and side1 not in allGlyphs:
                    continue
                if side2 not in side2Classes and side2 not in allGlyphs:
                    continue
                flags = (side1 in side1Classes, side2 in side2Classes)
                pairsByFlags.setdefault(flags, set()).add((side1, side2))

        result = []
        for flags, pairs in sorted(pairsByFlags.items()):
            for side1, side2 in sorted(pairs):
                value = VariableScalar()
                for source in designspace.sources:
                    if (side1, side2) in source.font.kerning:
                        location = get_userspace_location(designspace, source.location)
                        value.add_value(location, source.font.kerning[side1, side2])
                    elif source.font == default_font:
                        # Need to establish a default master value for the kern
                        location = get_userspace_location(designspace, source.location)
                        value.add_value(location, 0)
                values = list(value.values.values())
                value = collapse_varscalar(value)
                if all(flags) and value == 0:
                    # ignore zero-valued class kern pairs
                    continue
                firstIsClass, secondIsClass = flags
                if firstIsClass:
                    side1 = side1Classes[side1]
                if secondIsClass:
                    side2 = side2Classes[side2]
                result.append(KerningPair(side1, side2, value))
        return result
