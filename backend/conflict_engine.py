import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.canonical_schemas import (
    CorridorConflict, RailwayEvent, EventType, EventSeverity, EventSource,
    NormalizedTrainState, BlockState, PlanVersion
)
from backend.railway_state import RailwayStateStore, get_state_store

logger = logging.getLogger('railway.conflict_engine')

class ConflictDetectionEngine:
    def __init__(self, state_store: Optional[RailwayStateStore] = None):
        self.state_store = state_store or get_state_store()

    def evaluate_corridor(self) -> List[CorridorConflict]:
        trains = self.state_store.get_all_train_states()
        blocks = self.state_store.get_all_block_states()
        active_plan = self.state_store.get_active_plan()

        conflicts: List[CorridorConflict] = []
        conflicts.extend(self._check_block_collisions_and_headway(trains))
        conflicts.extend(self._check_speed_violations(trains, blocks))
        conflicts.extend(self._check_unexplained_occupancies(blocks, trains))
        conflicts.extend(self._check_schedule_drift(trains))
        conflicts.extend(self._check_maintenance_encroachment(trains, active_plan))

        for c in conflicts:
            self.state_store.record_conflict(c)
            evt = RailwayEvent(
                event_type=EventType.PLAN_CONFLICT_DETECTED,
                source=EventSource.OPERATOR,
                entity_id=c.conflict_id,
                section_id=c.section_id,
                timestamp=c.detected_at,
                severity=EventSeverity.CRITICAL if c.severity == 'CRITICAL' else EventSeverity.WARNING,
                title=f'Conflict Detected: {c.conflict_type}',
                description=c.description,
                payload={
                    'conflict_id': c.conflict_id,
                    'conflict_type': c.conflict_type,
                    'affected_trains': c.affected_trains,
                    'affected_blocks': c.affected_blocks,
                    'affected_tasks': c.affected_tasks,
                    'requires_reoptimization': c.requires_reoptimization
                },
                provenance={'engine': 'ConflictDetectionEngine'}
            )
            self.state_store.record_event(evt)

        return conflicts

    def _check_block_collisions_and_headway(self, trains: List[NormalizedTrainState]) -> List[CorridorConflict]:
        conflicts: List[CorridorConflict] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        section_trains: Dict[str, List[NormalizedTrainState]] = {}
        for t in trains:
            sec = t.current_section or 'UNKNOWN'
            section_trains.setdefault(sec, []).append(t)

        for sec, t_list in section_trains.items():
            if len(t_list) > 1:
                t_ids = [t.train_id for t in t_list]
                conflicts.append(CorridorConflict(
                    section_id=sec,
                    conflict_type='HEADWAY_VIOLATION',
                    severity='CRITICAL',
                    affected_trains=t_ids,
                    affected_blocks=[sec],
                    description=f'Multiple trains {t_ids} detected in section {sec} simultaneously. Safe block headway compromised.',
                    detected_at=now_iso,
                    requires_reoptimization=True
                ))

        return conflicts

    def _check_speed_violations(self, trains: List[NormalizedTrainState], blocks: List[BlockState]) -> List[CorridorConflict]:
        conflicts: List[CorridorConflict] = []
        now_iso = datetime.now(timezone.utc).isoformat()
        restricted_blocks = {b.section_id: b for b in blocks if b.restriction_status == 'RESTRICTED' and b.active_speed_limit_kmph is not None}

        for t in trains:
            blk = restricted_blocks.get(t.current_section)
            if blk and blk.active_speed_limit_kmph is not None:
                if t.speed_kmph > (blk.active_speed_limit_kmph + 5.0):
                    conflicts.append(CorridorConflict(
                        section_id=t.current_section,
                        conflict_type='SPEED_RESTRICTION_EXCEEDED',
                        severity='CRITICAL',
                        affected_trains=[t.train_id],
                        affected_blocks=[blk.block_id],
                        description=f'Train {t.train_id} operating at {t.speed_kmph} km/h in restricted section {t.current_section} (Limit: {blk.active_speed_limit_kmph} km/h).',
                        detected_at=now_iso,
                        requires_reoptimization=False
                    ))

        return conflicts

    def _check_unexplained_occupancies(self, blocks: List[BlockState], trains: List[NormalizedTrainState]) -> List[CorridorConflict]:
        conflicts: List[CorridorConflict] = []
        now_iso = datetime.now(timezone.utc).isoformat()
        reported_sections = {t.current_section for t in trains}

        for b in blocks:
            if b.occupancy_state == 'OCCUPIED' and not b.occupied_by:
                if b.section_id not in reported_sections:
                    conflicts.append(CorridorConflict(
                        section_id=b.section_id,
                        conflict_type='UNEXPLAINED_BLOCK_OCCUPANCY',
                        severity='WARNING',
                        affected_trains=[],
                        affected_blocks=[b.block_id],
                        description=f'Block {b.block_id} (Section {b.section_id}) indicates axle occupancy ({b.axle_count_balance} axles) with no identified scheduled service.',
                        detected_at=now_iso,
                        requires_reoptimization=True
                    ))

        return conflicts

    def _check_schedule_drift(self, trains: List[NormalizedTrainState]) -> List[CorridorConflict]:
        conflicts: List[CorridorConflict] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for t in trains:
            if t.delay_seconds >= 600:
                t_name = t.train_name or 'Service'
                conflicts.append(CorridorConflict(
                    section_id=t.current_section,
                    conflict_type='SCHEDULE_DRIFT_CASCADE',
                    severity='WARNING',
                    affected_trains=[t.train_id],
                    affected_blocks=[],
                    description=f'Train {t.train_id} ({t_name}) has accumulated {round(t.delay_seconds / 60.0, 1)} mins delay in {t.current_section}, triggering downstream slot conflicts.',
                    detected_at=now_iso,
                    requires_reoptimization=True
                ))

        return conflicts

    def _check_maintenance_encroachment(self, trains: List[NormalizedTrainState], active_plan: Optional[PlanVersion]) -> List[CorridorConflict]:
        conflicts: List[CorridorConflict] = []
        if not active_plan or not active_plan.scheduled_items:
            return conflicts

        now_iso = datetime.now(timezone.utc).isoformat()
        for item in active_plan.scheduled_items:
            task_sec = item.get('section_id')
            task_name = item.get('task_name')
            for t in trains:
                if t.current_section == task_sec and t.status == 'RUNNING':
                    conflicts.append(CorridorConflict(
                        section_id=task_sec,
                        conflict_type='MAINTENANCE_WINDOW_ENCROACHMENT',
                        severity='CRITICAL',
                        affected_trains=[t.train_id],
                        affected_tasks=[item.get('task_id', '')],
                        affected_blocks=[task_sec],
                        description=f'Train {t.train_id} active in section {task_sec} during planned maintenance block {task_name}. Re-optimization required.',
                        detected_at=now_iso,
                        requires_reoptimization=True
                    ))

        return conflicts

conflict_engine = ConflictDetectionEngine()

def get_conflict_engine() -> ConflictDetectionEngine:
    return conflict_engine
