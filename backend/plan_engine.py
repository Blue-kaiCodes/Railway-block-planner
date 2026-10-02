import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.canonical_schemas import (
    PlanVersion, PlanDiffItem, PlanApprovalStatus, RailwayEvent,
    EventType, EventSeverity, EventSource, NormalizedTrainState, BlockState
)
from backend.railway_state import RailwayStateStore, get_state_store
from backend.optimizer import run_optimization
from backend.database import db

logger = logging.getLogger('railway.plan_engine')

class PlanEngine:
    def __init__(self, state_store: Optional[RailwayStateStore] = None):
        self.state_store = state_store or get_state_store()

    def get_next_plan_id(self) -> tuple[str, int]:
        all_plans = self.state_store.get_all_plan_versions()
        if not all_plans:
            return 'PLAN-001', 1
        max_v = max(p.version_number for p in all_plans)
        next_v = max_v + 1
        return f'PLAN-{next_v:03d}', next_v

    def generate_candidate_plan(self, triggered_by: str = 'LIVE_TELEMETRY', reason: str = 'Real-time schedule re-optimization') -> PlanVersion:
        now_iso = datetime.now(timezone.utc).isoformat()
        plan_id, version_num = self.get_next_plan_id()

        tasks = db.get_tasks()
        trains = db.get_trains()
        block_windows = db.get_block_windows()
        resources = db.get_resources()

        live_trains = self.state_store.get_all_train_states()
        live_blocks = self.state_store.get_all_block_states()

        train_delays = {t.train_id: t.delay_seconds / 60.0 for t in live_trains}
        train_sections = {t.train_id: t.current_section for t in live_trains}

        adjusted_trains = []
        for tr in trains:
            t_copy = dict(tr)
            tid = t_copy.get('train_id', '')
            delay_mins = train_delays.get(tid, 0.0)
            delay_hours = delay_mins / 60.0

            if delay_hours > 0:
                t_copy['arrival_hour'] = round(t_copy['arrival_hour'] + delay_hours, 2)
                t_copy['departure_hour'] = round(t_copy['departure_hour'] + delay_hours, 2)
                t_copy['is_delayed'] = True
                t_copy['delay_mins'] = round(delay_mins, 1)

            t_sec = train_sections.get(tid, t_copy.get('section'))
            for blk in live_blocks:
                if blk.section_id == t_sec and blk.restriction_status == 'RESTRICTED' and blk.active_speed_limit_kmph:
                    slowdown_factor = max(1.0, 90.0 / max(blk.active_speed_limit_kmph, 15.0))
                    original_dur = t_copy['departure_hour'] - t_copy['arrival_hour']
                    expanded_dur = original_dur * slowdown_factor
                    t_copy['departure_hour'] = round(t_copy['arrival_hour'] + expanded_dur, 2)

            adjusted_trains.append(t_copy)

        adjusted_windows = []
        closed_sections = {b.section_id for b in live_blocks if b.restriction_status == 'RESTRICTED' and b.active_speed_limit_kmph == 0.0}
        for bw in block_windows:
            if bw.get('section') not in closed_sections:
                adjusted_windows.append(bw)

        active_plan = self.state_store.get_active_plan()
        prev_scheduled = active_plan.scheduled_items if active_plan else None

        result = run_optimization(
            tasks=tasks,
            trains=adjusted_trains,
            block_windows=adjusted_windows,
            resources=resources,
            previous_schedule=prev_scheduled
        )

        diff_items = self._compute_plan_diff(prev_scheduled or [], result.get('scheduled_items', []), train_delays)

        sched_count = len(result.get('scheduled_items', []))
        unsched_count = len(result.get('unassigned_tasks', []))
        summary_text = f'Re-optimized plan generated ({sched_count} tasks scheduled, {unsched_count} unassigned). Triggered by: {triggered_by}. Reason: {reason}.'

        plan = PlanVersion(
            plan_id=plan_id,
            version_number=version_num,
            status=PlanApprovalStatus.PENDING_APPROVAL,
            triggered_by=triggered_by,
            trigger_reason=reason,
            solver_status=result.get('solver_status', 'UNKNOWN'),
            solve_time_seconds=result.get('solve_time_seconds', 0.0),
            objective_value=result.get('objective_value', 0.0),
            tasks_scheduled=result.get('total_tasks_scheduled', 0),
            tasks_unscheduled=len(result.get('unassigned_tasks', [])),
            scheduled_items=result.get('scheduled_items', []),
            unassigned_tasks=result.get('unassigned_tasks', []),
            diff=diff_items,
            summary=summary_text,
            created_at=now_iso
        )

        self.state_store.save_plan_version(plan)

        self.state_store.record_event(RailwayEvent(
            event_type=EventType.CANDIDATE_PLAN_GENERATED,
            source=EventSource.OPERATOR,
            entity_id=plan.plan_id,
            timestamp=now_iso,
            severity=EventSeverity.INFO,
            title=f'Candidate Plan Generated: {plan.plan_id}',
            description=f'{plan.plan_id} (Version {version_num}) awaiting Chief Controller approval. {len(diff_items)} shift diffs detected.',
            payload={
                'plan_id': plan.plan_id,
                'version_number': version_num,
                'tasks_scheduled': plan.tasks_scheduled,
                'diff_count': len(diff_items)
            },
            provenance={'engine': 'PlanEngine', 'solver': 'Google OR-Tools CP-SAT'}
        ))

        return plan

    def _compute_plan_diff(self, old_items: List[Dict[str, Any]], new_items: List[Dict[str, Any]], train_delays: Dict[str, float]) -> List[PlanDiffItem]:
        diffs: List[PlanDiffItem] = []
        old_map = {item['task_id']: item for item in old_items}
        new_map = {item['task_id']: item for item in new_items}

        all_task_ids = set(old_map.keys()).union(set(new_map.keys()))

        for tid in sorted(all_task_ids):
            old = old_map.get(tid)
            new = new_map.get(tid)

            if old and not new:
                diffs.append(PlanDiffItem(
                    task_id=tid,
                    task_name=old.get('task_name', tid),
                    action='UNASSIGNED',
                    section_id=old.get('section', ''),
                    old_start_hour=old.get('start_hour'),
                    old_end_hour=old.get('end_hour'),
                    impact_reason='Corridor delay / capacity constriction forced task unscheduling.'
                ))
            elif not old and new:
                diffs.append(PlanDiffItem(
                    task_id=tid,
                    task_name=new.get('task_name', tid),
                    action='NEWLY_SCHEDULED',
                    section_id=new.get('section', ''),
                    new_start_hour=new.get('start_hour'),
                    new_end_hour=new.get('end_hour'),
                    impact_reason='Capacity available to accommodate previously deferred task.'
                ))
            elif old and new:
                shift_mins = round((new.get('start_hour', 0.0) - old.get('start_hour', 0.0)) * 60.0)
                sec_changed = old.get('section') != new.get('section')
                if abs(shift_mins) > 1 or sec_changed:
                    action = 'SHIFTED' if abs(shift_mins) > 1 else 'UNCHANGED'
                    direction_str = 'later' if shift_mins > 0 else 'earlier'
                    reason = f'Adjusted {abs(shift_mins)}m {direction_str} to resolve corridor train conflict.'
                    diffs.append(PlanDiffItem(
                        task_id=tid,
                        task_name=new.get('task_name', tid),
                        action=action,
                        section_id=new.get('section', ''),
                        old_start_hour=old.get('start_hour'),
                        old_end_hour=old.get('end_hour'),
                        new_start_hour=new.get('start_hour'),
                        new_end_hour=new.get('end_hour'),
                        shift_minutes=shift_mins,
                        impact_reason=reason
                    ))

        return diffs

    def approve_candidate_plan(self, plan_id: str, reviewer: str = 'Chief Controller', comments: Optional[str] = None) -> PlanVersion:
        plan = self.state_store.get_plan_version(plan_id)
        if not plan:
            raise ValueError(f'Plan {plan_id} not found')
        if plan.status != PlanApprovalStatus.PENDING_APPROVAL:
            raise ValueError(f'Plan {plan_id} is in status {plan.status.value}, cannot approve.')

        now_iso = datetime.now(timezone.utc).isoformat()

        active = self.state_store.get_active_plan()
        if active and active.plan_id != plan_id:
            active.status = PlanApprovalStatus.SUPERSEDED
            self.state_store.save_plan_version(active)

        plan.status = PlanApprovalStatus.APPROVED
        plan.reviewed_at = now_iso
        plan.reviewed_by = reviewer
        if comments:
            plan.summary += f' Controller comments: {comments}'
        self.state_store.save_plan_version(plan)

        conflicts = self.state_store.get_unresolved_conflicts()
        for c in conflicts:
            self.state_store.resolve_conflict(c.conflict_id)

        self.state_store.record_event(RailwayEvent(
            event_type=EventType.PLAN_APPROVED,
            source=EventSource.OPERATOR,
            entity_id=plan.plan_id,
            timestamp=now_iso,
            severity=EventSeverity.INFO,
            title=f'Plan Approved: {plan.plan_id}',
            description=f'Plan {plan.plan_id} formally approved by {reviewer}. Active operational plan updated.',
            payload={'plan_id': plan.plan_id, 'approved_by': reviewer, 'comments': comments},
            provenance={'operator': reviewer, 'role': 'CHIEF_CONTROLLER'}
        ))

        return plan

    def reject_candidate_plan(self, plan_id: str, reviewer: str = 'Chief Controller', reason: str = 'Rejected by Controller') -> PlanVersion:
        plan = self.state_store.get_plan_version(plan_id)
        if not plan:
            raise ValueError(f'Plan {plan_id} not found')
        if plan.status != PlanApprovalStatus.PENDING_APPROVAL:
            raise ValueError(f'Plan {plan_id} is in status {plan.status.value}, cannot reject.')

        now_iso = datetime.now(timezone.utc).isoformat()
        plan.status = PlanApprovalStatus.REJECTED
        plan.reviewed_at = now_iso
        plan.reviewed_by = reviewer
        plan.rejection_reason = reason
        self.state_store.save_plan_version(plan)

        self.state_store.record_event(RailwayEvent(
            event_type=EventType.PLAN_REJECTED,
            source=EventSource.OPERATOR,
            entity_id=plan.plan_id,
            timestamp=now_iso,
            severity=EventSeverity.WARNING,
            title=f'Plan Rejected: {plan.plan_id}',
            description=f'Plan {plan.plan_id} rejected by {reviewer}. Reason: {reason}. Previous active plan retained.',
            payload={'plan_id': plan.plan_id, 'rejected_by': reviewer, 'reason': reason},
            provenance={'operator': reviewer, 'role': 'CHIEF_CONTROLLER'}
        ))

        return plan

plan_engine = PlanEngine()

def get_plan_engine() -> PlanEngine:
    return plan_engine
