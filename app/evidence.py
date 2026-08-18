from typing import List
from .schemas import (
    Evidence,
    ReviewedTranscriptSegment,
)


def attach_evidence(
    segment_ids: List[str],
    segments: List[ReviewedTranscriptSegment],
) -> List[Evidence]:
    segment_map = {
        segment.segment_id: segment
        for segment in segments
    }

    evidence_list = []

    for segment_id in segment_ids:
        segment = segment_map.get(segment_id)

        if segment is None:
            continue

        evidence_list.append(
            Evidence(
                segment_id=segment.segment_id,
                quote=segment.text,
                speaker=segment.speaker,
                start_time=segment.start_time,
                end_time=segment.end_time,
            )
        )

    return evidence_list
