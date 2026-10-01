"""Tests for the identifier scanner. Run: cd labllm && uv run --with pytest pytest ../tests"""
from labllm.scan import IdentifierError, scan_text


def kinds(text, **kw):
    return {f.kind for f in scan_text(text, **kw)}


def test_direct_identifiers():
    t = ("Email me at jane.doe@cornell.edu or call (607) 555-0123.\n"
         "SSN 123-45-6789, NetID jd123, student ID 4412345.\n"
         "Born March 14, 2001; lives at 12 College Avenue, Ithaca NY 14850.\n"
         "See linkedin.com/in/janedoe and @janedoe_eng. Dr. Smith agreed.")
    got = kinds(t)
    for k in ["email", "phone", "ssn", "netid", "student_id", "date", "street_address",
              "zip_code", "profile_url", "social_handle", "titled_name"]:
        assert k in got, k


def test_clean_deidentified_text_passes():
    t = ("P03: I think the AI tool changed how I grade the design reports.\n"
         "Interviewer: Can you say more about that?\n"
         "P03: In ME courses in 2024 we saw more polished but shallower work.")
    assert scan_text(t) == []


def test_speaker_labels():
    assert "speaker_name" in kinds("Jane Doe: I teach statics.\n")
    assert "speaker_name" not in kinds("Participant Three: I teach statics.\n")


def test_names_list_and_allow():
    t = "Maria said the rubric was unclear. Alex agreed."
    assert kinds(t, names=["Maria"]) == {"listed_name"}
    assert scan_text(t, names=["Maria"], allow=["Maria"]) == []


def test_masking_never_reveals_full_value():
    f = scan_text("contact jane.doe@cornell.edu")[0]
    assert "jane.doe@cornell.edu" not in str(f)


def test_ignore_kind():
    assert "date" not in kinds("Interview on 03/14/2024", ignore=["date"])


def test_error_message_lists_kinds():
    e = IdentifierError(scan_text("jd123 wrote to jane@x.org"))
    assert "email" in str(e) and "netid" in str(e)
