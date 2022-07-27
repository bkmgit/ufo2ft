import io
from textwrap import dedent

import pytest
from fontTools import designspaceLib

from ufo2ft import compileVariableTTF


def test_variable_features(FontClass):
    tmp = io.StringIO()
    designspace = designspaceLib.DesignSpaceDocument.fromfile(
        "tests/data/TestVarfea.designspace"
    )
    designspace.loadSourceFonts(FontClass)
    varfont = compileVariableTTF(designspace, debugFeatureFile=tmp)

    assert dedent("\n" + tmp.getvalue()) == dedent(
        """
        conditionset ConditionSet1 {
            wght 600 1000;
        } ConditionSet1;

        variation rvrn ConditionSet1 {
            sub peh-ar.init by peh-ar.init.BRACKET.600;
        } rvrn;

        feature curs {
            lookup curs {
                lookupflag RightToLeft IgnoreMarks;
                pos cursive alef-ar.fina <anchor (wght=100:299 wght=1000:299) (wght=100:97 wght=1000:97)> <anchor NULL>;
                pos cursive peh-ar.init <anchor NULL> <anchor (wght=100:161 wght=1000:161) (wght=100:54 wght=1000:54)>;
                pos cursive peh-ar.init.BRACKET.600 <anchor NULL> <anchor (wght=100:89 wght=1000:89) (wght=100:53 wght=1000:53)>;
            } curs;

        } curs;
"""
    )
