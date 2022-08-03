from __future__ import annotations

from typing import Any

from fontTools.designspaceLib import AxisDescriptor
from fontTools.feaLib import ast
from fontTools.varLib import FEAVAR_FEATURETAG_LIB_KEY

from ufo2ft.featureWriters import BaseFeatureWriter


class VariableRulesFeatureWriter(BaseFeatureWriter):
    def write(self, font, feaFile, compiler=None):
        """Write features and class definitions for this font to a feaLib
        FeatureFile object.

        Returns True if feature file was modified, False if no new features were
        generated.
        """
        self.setContext(font, feaFile, compiler=compiler)
        return self._write()

    def _write(self):
        self._designspace = self.context.font
        axis_map = {axis.name: axis for axis in self._designspace.axes}

        feature_tag = self._designspace.lib.get(
            FEAVAR_FEATURETAG_LIB_KEY,
            "rclt" if self._designspace.rulesProcessingLast else "rvrn",
        )

        # TODO: Generate one lookup per rule and link all condition sets to it.
        # Currently, each conditionset will generate a new identical lookup.
        feaFile = self.context.feaFile
        self._conditionsets = []
        for rule in self._designspace.rules:
            conditionsets = transform_condition_sets(rule.conditionSets, axis_map)
            for conditionset in conditionsets:
                if conditionset not in self._conditionsets:
                    cs_name = "ConditionSet%i" % (len(self._conditionsets) + 1)
                    feaFile.statements.append(
                        ast.ConditionsetStatement(cs_name, conditionset)
                    )
                    self._conditionsets.append(conditionset)
                else:
                    cs_name = "ConditionSet%i" % self._conditionsets.index(conditionset)
                block = ast.VariationBlock(feature_tag, cs_name)
                for sub in rule.subs:
                    block.statements.append(
                        ast.SingleSubstStatement(
                            [ast.GlyphName(sub[0])],
                            [ast.GlyphName(sub[1])],
                            [],
                            [],
                            False,
                        )
                    )
                feaFile.statements.append(block)


def transform_condition_sets(
    condition_sets: list[list[dict[str, Any]]],
    axis_map: dict[str, AxisDescriptor],
) -> list[dict[str, tuple[float, float]]]:
    """Returns condition sets shoved into dicts with values in userspace."""

    new_condition_sets = []
    for condition_set in condition_sets:
        new_condition = {}
        for rule in condition_set:
            axis = axis_map[rule["name"]]
            tag = axis.tag
            new_condition[tag] = (
                axis.map_backward(rule["minimum"]),
                axis.map_backward(rule["maximum"]),
            )
        new_condition_sets.append(new_condition)
    return new_condition_sets
