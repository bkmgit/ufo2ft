from fontTools.feaLib.variableScalar import VariableScalar

from ufo2ft.featureWriters import CursFeatureWriter, ast
from ufo2ft.util import get_userspace_location


class VariableCursFeatureWriter(CursFeatureWriter):
    def _getAnchors(self, glyphName, glyph=None):
        entry_anchor = None
        exit_anchor = None
        entry_x_value = VariableScalar()
        entry_y_value = VariableScalar()
        exit_x_value = VariableScalar()
        exit_y_value = VariableScalar()
        for source in self.context.font.sources:
            for anchor in glyph.anchors:
                if anchor.name == "entry":
                    location = get_userspace_location(
                        self.context.font, source.location
                    )
                    entry_x_value.add_value(location, anchor.x)
                    entry_y_value.add_value(location, anchor.y)
                    if entry_anchor is None:
                        entry_anchor = ast.Anchor(x=entry_x_value, y=entry_y_value)
                if anchor.name == "exit":
                    location = get_userspace_location(
                        self.context.font, source.location
                    )
                    exit_x_value.add_value(location, anchor.x)
                    exit_y_value.add_value(location, anchor.y)
                    if exit_anchor is None:
                        exit_anchor = ast.Anchor(x=exit_x_value, y=exit_y_value)
        return entry_anchor, exit_anchor
