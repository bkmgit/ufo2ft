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
        if glyphSet:
            allGlyphs = set(glyphSet.keys())
        else:
            default_source = designspace.findDefault()
            assert default_source is not None and default_source.font is not None
            allGlyphs = set(default_source.font.keys())
        side1Groups: dict[str, list[str]] = {}
        side2Groups: dict[str, list[str]] = {}
        for source in designspace.sources:
            font = source.font
            assert font is not None
            for name, members in font.groups.items():
                # prune non-existent or skipped glyphs
                members = {g for g in members if g in allGlyphs}
                # skip empty groups
                if not members:
                    continue
                # skip groups without UFO3 public.kern{1,2} prefix
                if name.startswith(SIDE1_PREFIX):
                    group = side1Groups.get(name)
                    if group is None:
                        side1Groups[name] = sorted(members)
                    elif set(group) != members:
                        log_redefined_group("left", name, group, font, members)
                elif name.startswith(SIDE2_PREFIX):
                    group = side2Groups.get(name)
                    if group is None:
                        side2Groups[name] = sorted(members)
                    elif set(group) != members:
                        log_redefined_group("right", name, group, font, members)
        return side1Groups, side2Groups

    @staticmethod
    def getKerningPairs(designspace, side1Classes, side2Classes, glyphSet=None):
        default_font = designspace.findDefault().font
        if glyphSet:
            allGlyphs = set(glyphSet.keys())
        else:
            allGlyphs = set(default_font.keys())

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
                    location = get_userspace_location(designspace, source.location)
                    if (side1, side2) in source.font.kerning:
                        value.add_value(location, source.font.kerning[side1, side2])
                    else:
                        # We assume that any missing kern values are zero.
                        # It would be really nice to be able to omit missing kern
                        # values from the variable scalar; that way, they would
                        # be interpolated, and that would mean that designers
                        # wouldn't need to add explicit kerns for intermediate masters
                        # where interpolation would do the right thing.
                        # But there isn't a way to do that and still be backwards
                        # compatible with previous versions - in previous versions,
                        # explicitly zero kern values would be dropped when writing the
                        # master-specific binary TTFs, so when merging we had to
                        # assume that any missing values were zero.
                        # So we do the same here.
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


def log_redefined_group(
    side: str, name: str, group: list[str], font: Any, members: set[str]
) -> None:
    log.warning(
        "incompatible %s groups: %s was previously %s, %s tried to make it %s",
        side,
        name,
        sorted(group),
        font,
        sorted(members),
    )
