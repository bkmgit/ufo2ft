from __future__ import annotations

import logging
from typing import Any

from fontTools.designspaceLib import DesignSpaceDocument
from fontTools.feaLib.variableScalar import VariableScalar

from ufo2ft.featureWriters import KernFeatureWriter
from ufo2ft.featureWriters.kernFeatureWriter import (
    SIDE1_PREFIX,
    SIDE2_PREFIX,
    KerningPair,
)
from ufo2ft.util import collapse_varscalar, get_userspace_location

log = logging.getLogger(__file__)


class VariableKernFeatureWriter(KernFeatureWriter):
    @staticmethod
    def getKerningGroups(
        designspace: DesignSpaceDocument, glyphSet: dict[str, Any] | None = None
    ) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
        default_source = designspace.findDefault()
        assert default_source is not None and default_source.font is not None
        if glyphSet:
            allGlyphs = set(glyphSet.keys())
        else:
            allGlyphs = set(default_source.font.keys())
        side1Groups: dict[str, list[str]] = {}
        side2Groups: dict[str, list[str]] = {}
        # only consider the groups from the default source, as we do for
        # instance generation.
        for name, members in default_source.font.groups.items():
            # prune non-existent or skipped glyphs
            members = {g for g in members if g in allGlyphs}
            # skip empty groups
            if not members:
                continue
            # skip groups without UFO3 public.kern{1,2} prefix
            if name.startswith(SIDE1_PREFIX):
                side1Groups[name] = sorted(members)
            elif name.startswith(SIDE2_PREFIX):
                side2Groups[name] = sorted(members)
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
