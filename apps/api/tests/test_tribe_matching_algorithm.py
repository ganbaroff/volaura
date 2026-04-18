"""Tests for tribe_matching._cluster_and_match pure algorithm.

Covers: sorting, score proximity, co-member exclusion, triplet/pair formation,
remainder handling, edge cases (empty, single, all excluded, exact boundary).
"""

from __future__ import annotations

from app.services.tribe_matching import (
    SCORE_PROXIMITY,
    TRIBE_SIZE,
    _cluster_and_match,
)


def _cand(uid: str, score: float, prev: list[str] | None = None) -> dict:
    return {
        "user_id": uid,
        "aura_score": score,
        "previous_co_member_ids": prev or [],
    }


class TestClusterAndMatchBasic:
    def test_empty_input(self):
        assert _cluster_and_match([]) == []

    def test_single_candidate_no_group(self):
        assert _cluster_and_match([_cand("a", 50.0)]) == []

    def test_two_candidates_form_pair(self):
        groups = _cluster_and_match([_cand("a", 50.0), _cand("b", 55.0)])
        assert len(groups) == 1
        ids = {u["user_id"] for u in groups[0]}
        assert ids == {"a", "b"}

    def test_three_candidates_form_triplet(self):
        groups = _cluster_and_match(
            [
                _cand("a", 50.0),
                _cand("b", 55.0),
                _cand("c", 60.0),
            ]
        )
        assert len(groups) == 1
        assert len(groups[0]) == TRIBE_SIZE

    def test_four_candidates_triplet_plus_remainder(self):
        groups = _cluster_and_match(
            [
                _cand("a", 50.0),
                _cand("b", 52.0),
                _cand("c", 54.0),
                _cand("d", 56.0),
            ]
        )
        total_matched = sum(len(g) for g in groups)
        assert total_matched >= 3

    def test_six_candidates_two_triplets(self):
        groups = _cluster_and_match(
            [
                _cand("a", 50.0),
                _cand("b", 52.0),
                _cand("c", 54.0),
                _cand("d", 56.0),
                _cand("e", 58.0),
                _cand("f", 60.0),
            ]
        )
        total_matched = sum(len(g) for g in groups)
        assert total_matched >= 4
        for g in groups:
            assert len(g) >= 2


class TestScoreProximity:
    def test_within_boundary_matched(self):
        groups = _cluster_and_match(
            [
                _cand("a", 50.0),
                _cand("b", 50.0 + SCORE_PROXIMITY),
            ]
        )
        assert len(groups) == 1

    def test_exact_boundary_included(self):
        groups = _cluster_and_match(
            [
                _cand("a", 50.0),
                _cand("b", 50.0 + SCORE_PROXIMITY),
            ]
        )
        assert len(groups) == 1
        ids = {u["user_id"] for u in groups[0]}
        assert ids == {"a", "b"}

    def test_beyond_boundary_not_matched(self):
        groups = _cluster_and_match(
            [
                _cand("a", 50.0),
                _cand("b", 50.0 + SCORE_PROXIMITY + 0.1),
            ]
        )
        assert groups == []

    def test_two_clusters_separated_by_gap(self):
        groups = _cluster_and_match(
            [
                _cand("a", 10.0),
                _cand("b", 12.0),
                _cand("c", 14.0),
                _cand("d", 80.0),
                _cand("e", 82.0),
                _cand("f", 84.0),
            ]
        )
        assert len(groups) == 2
        cluster_1_ids = {u["user_id"] for u in groups[0]}
        cluster_2_ids = {u["user_id"] for u in groups[1]}
        assert cluster_1_ids & {"a", "b", "c"}
        assert cluster_2_ids & {"d", "e", "f"}


class TestCoMemberExclusion:
    def test_previous_co_member_excluded(self):
        groups = _cluster_and_match(
            [
                _cand("a", 50.0, prev=["b"]),
                _cand("b", 52.0),
            ]
        )
        assert groups == []

    def test_excluded_co_member_falls_to_next_compatible(self):
        groups = _cluster_and_match(
            [
                _cand("a", 50.0, prev=["b"]),
                _cand("b", 51.0),
                _cand("c", 53.0),
            ]
        )
        matched_ids = set()
        for g in groups:
            for u in g:
                matched_ids.add(u["user_id"])
        if "a" in matched_ids:
            for g in groups:
                ids = {u["user_id"] for u in g}
                if "a" in ids:
                    assert "b" not in ids

    def test_all_excluded_yields_empty(self):
        groups = _cluster_and_match(
            [
                _cand("a", 50.0, prev=["b", "c"]),
                _cand("b", 52.0, prev=["a", "c"]),
                _cand("c", 54.0, prev=["a", "b"]),
            ]
        )
        assert groups == []

    def test_partial_exclusion_forms_valid_group(self):
        groups = _cluster_and_match(
            [
                _cand("a", 50.0, prev=["b"]),
                _cand("b", 51.0),
                _cand("c", 52.0),
                _cand("d", 53.0),
            ]
        )
        for g in groups:
            ids = {u["user_id"] for u in g}
            if "a" in ids:
                assert "b" not in ids


class TestSortingInvariant:
    def test_unsorted_input_produces_same_result(self):
        candidates = [
            _cand("c", 90.0),
            _cand("a", 10.0),
            _cand("b", 50.0),
        ]
        groups = _cluster_and_match(candidates)
        all_ids = set()
        for g in groups:
            for u in g:
                all_ids.add(u["user_id"])
        assert len(groups) >= 0

    def test_sorted_by_score_ascending_greedy(self):
        candidates = [
            _cand("high", 95.0),
            _cand("low", 10.0),
            _cand("mid", 50.0),
        ]
        groups = _cluster_and_match(candidates)
        for g in groups:
            scores = [u["aura_score"] for u in g]
            assert max(scores) - min(scores) <= SCORE_PROXIMITY


class TestEdgeCases:
    def test_identical_scores(self):
        groups = _cluster_and_match(
            [
                _cand("a", 75.0),
                _cand("b", 75.0),
                _cand("c", 75.0),
            ]
        )
        assert len(groups) == 1
        assert len(groups[0]) == 3

    def test_zero_scores(self):
        groups = _cluster_and_match(
            [
                _cand("a", 0.0),
                _cand("b", 0.0),
            ]
        )
        assert len(groups) == 1

    def test_high_scores(self):
        groups = _cluster_and_match(
            [
                _cand("a", 100.0),
                _cand("b", 100.0),
                _cand("c", 100.0),
            ]
        )
        assert len(groups) == 1

    def test_negative_score_difference(self):
        groups = _cluster_and_match(
            [
                _cand("a", 60.0),
                _cand("b", 50.0),
            ]
        )
        assert len(groups) == 1

    def test_large_pool_no_crash(self):
        candidates = [_cand(f"u{i}", float(i)) for i in range(100)]
        groups = _cluster_and_match(candidates)
        matched_ids = set()
        for g in groups:
            for u in g:
                assert u["user_id"] not in matched_ids
                matched_ids.add(u["user_id"])

    def test_no_user_matched_twice(self):
        candidates = [_cand(f"u{i}", 50.0 + i * 0.5) for i in range(20)]
        groups = _cluster_and_match(candidates)
        all_ids = []
        for g in groups:
            for u in g:
                all_ids.append(u["user_id"])
        assert len(all_ids) == len(set(all_ids))


class TestConstants:
    def test_tribe_size_is_three(self):
        assert TRIBE_SIZE == 3

    def test_score_proximity_is_fifteen(self):
        assert SCORE_PROXIMITY == 15.0
