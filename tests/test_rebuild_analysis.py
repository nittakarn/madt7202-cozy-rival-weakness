import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rebuild_analysis import TOPICS, topic_hits


def test_bare_feature_mention_is_not_a_complaint():
    assert "Story & Characters" not in topic_hits("The story has a cat and a character creator.")


def test_clear_story_complaint_is_coded():
    assert "Story & Characters" in topic_hits("The story is boring and the dialogue is flat.")


def test_clear_progression_complaint_is_coded():
    assert "Progression & Pacing" in topic_hits("The progression is slow and grindy.")


def test_all_feature_topics_have_patterns():
    assert all(TOPICS.values())
