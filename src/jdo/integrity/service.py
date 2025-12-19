"""IntegrityService for Honor-Your-Word protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlmodel import Session, func, select

from jdo.models.cleanup_plan import CleanupPlan, CleanupPlanStatus
from jdo.models.commitment import Commitment, CommitmentStatus
from jdo.models.integrity_metrics import (
    TREND_THRESHOLD,
    IntegrityMetrics,
    TrendDirection,
)
from jdo.models.stakeholder import Stakeholder
from jdo.models.task import Task, TaskStatus
from jdo.models.task_history import TaskEventType, TaskHistoryEntry

# Constants for risk detection
HOURS_24 = 24
HOURS_48 = 48
MAX_DISPLAY_ITEMS = 3  # Maximum items to show in risk summary message

# Constants for estimation accuracy calculation
MIN_TASKS_FOR_ACCURACY = 5  # Minimum tasks with estimates to calculate accuracy
ACCURACY_DECAY_DAYS = 7  # Weight halves every 7 days
ACCURACY_MAX_AGE_DAYS = 90  # Maximum age for history consideration

# Constants for trend calculation
TREND_PERIOD_DAYS = 30  # Period for comparing metrics (30 days)
AFFECTING_SCORE_DAYS = 30  # Days to look back for affecting commitments
MAX_AFFECTING_COMMITMENTS = 5  # Maximum commitments to show in affecting list


@dataclass
class RiskSummary:
    """Summary of detected risks on application launch."""

    overdue_commitments: list[Commitment] = field(default_factory=list)
    due_soon_commitments: list[Commitment] = field(default_factory=list)
    stalled_commitments: list[Commitment] = field(default_factory=list)

    @property
    def total_risks(self) -> int:
        """Total number of at-risk items."""
        return (
            len(self.overdue_commitments)
            + len(self.due_soon_commitments)
            + len(self.stalled_commitments)
        )

    @property
    def has_risks(self) -> bool:
        """Check if any risks were detected."""
        return self.total_risks > 0

    def to_message(self) -> str:
        """Generate a user-friendly message about detected risks."""
        if not self.has_risks:
            return ""

        lines: list[str] = []
        self._format_overdue_section(lines)
        self._format_due_soon_section(lines)
        self._format_stalled_section(lines)
        return "\n".join(lines)

    def _format_overdue_section(self, lines: list[str]) -> None:
        """Format the overdue commitments section."""
        if not self.overdue_commitments:
            return
        count = len(self.overdue_commitments)
        lines.append(f"**{count} overdue commitment(s):**")
        lines.extend(
            f"  - {c.deliverable} (due {c.due_date})"
            for c in self.overdue_commitments[:MAX_DISPLAY_ITEMS]
        )
        if count > MAX_DISPLAY_ITEMS:
            lines.append(f"  ... and {count - MAX_DISPLAY_ITEMS} more")
        lines.append("")

    def _format_due_soon_section(self, lines: list[str]) -> None:
        """Format the due soon commitments section."""
        if not self.due_soon_commitments:
            return
        count = len(self.due_soon_commitments)
        lines.append(f"**{count} commitment(s) due within 24 hours:**")
        lines.extend(
            f"  - {c.deliverable} (due {c.due_date})"
            for c in self.due_soon_commitments[:MAX_DISPLAY_ITEMS]
        )
        if count > MAX_DISPLAY_ITEMS:
            lines.append(f"  ... and {count - MAX_DISPLAY_ITEMS} more")
        lines.append("")

    def _format_stalled_section(self, lines: list[str]) -> None:
        """Format the stalled commitments section."""
        if not self.stalled_commitments:
            return
        count = len(self.stalled_commitments)
        lines.append(f"**{count} stalled commitment(s):**")
        lines.extend(f"  - {c.deliverable}" for c in self.stalled_commitments[:MAX_DISPLAY_ITEMS])
        if count > MAX_DISPLAY_ITEMS:
            lines.append(f"  ... and {count - MAX_DISPLAY_ITEMS} more")


@dataclass
class AtRiskResult:
    """Result of marking a commitment as at-risk."""

    commitment: Commitment
    cleanup_plan: CleanupPlan
    notification_task: Task


@dataclass
class RecoveryResult:
    """Result of recovering a commitment from at-risk status."""

    commitment: Commitment
    cleanup_plan: CleanupPlan | None
    notification_task: Task | None
    notification_still_needed: bool


@dataclass
class AffectingCommitment:
    """A commitment that negatively affected the integrity score."""

    commitment: Commitment
    reason: str  # Why it affected the score (e.g., "completed late", "abandoned")


class IntegrityService:
    """Service for managing the Honor-Your-Word integrity protocol.

    This service handles:
    - Marking commitments as at-risk
    - Creating cleanup plans and notification tasks
    - Calculating integrity metrics from commitment history
    """

    def mark_commitment_at_risk(
        self,
        session: Session,
        commitment_id: UUID,
        reason: str,
        impact_description: str | None = None,
    ) -> AtRiskResult:
        """Mark a commitment as at-risk and start the cleanup workflow.

        This creates:
        1. Updates commitment status to at_risk
        2. Creates or reuses CleanupPlan
        3. Creates notification task at position 0

        Args:
            session: Database session
            commitment_id: ID of commitment to mark at-risk
            reason: Why the commitment is at risk
            impact_description: Optional description of impact

        Returns:
            AtRiskResult with updated entities
        """
        # Get commitment
        commitment = session.get(Commitment, commitment_id)
        if commitment is None:
            msg = f"Commitment {commitment_id} not found"
            raise ValueError(msg)

        # Get stakeholder name for notification task
        stakeholder = session.get(Stakeholder, commitment.stakeholder_id)
        stakeholder_name = stakeholder.name if stakeholder else "stakeholder"

        # Update commitment status
        commitment.status = CommitmentStatus.AT_RISK
        commitment.marked_at_risk_at = datetime.now(UTC)
        commitment.updated_at = datetime.now(UTC)
        session.add(commitment)

        # Get or create cleanup plan
        cleanup_plan = session.exec(
            select(CleanupPlan).where(CleanupPlan.commitment_id == commitment_id)
        ).first()

        if cleanup_plan is None:
            cleanup_plan = CleanupPlan(
                commitment_id=commitment_id,
                impact_description=impact_description,
                status=CleanupPlanStatus.PLANNED,
            )
            session.add(cleanup_plan)
            session.flush()  # Get ID

        # Check for existing notification task
        existing_task = session.exec(
            select(Task).where(
                Task.commitment_id == commitment_id,
                Task.is_notification_task == True,  # noqa: E712
            )
        ).first()

        if existing_task is None:
            # Create notification task
            notification_task = Task(
                commitment_id=commitment_id,
                title=f"Notify {stakeholder_name} about at-risk commitment",
                scope=self._generate_notification_scope(
                    commitment=commitment,
                    stakeholder_name=stakeholder_name,
                    reason=reason,
                    impact_description=impact_description,
                ),
                order=0,
                is_notification_task=True,
                status=TaskStatus.PENDING,
            )
            session.add(notification_task)
            session.flush()

            # Link cleanup plan to task
            cleanup_plan.notification_task_id = notification_task.id
            session.add(cleanup_plan)
        else:
            notification_task = existing_task

        session.commit()

        return AtRiskResult(
            commitment=commitment,
            cleanup_plan=cleanup_plan,
            notification_task=notification_task,
        )

    def recover_commitment(
        self,
        session: Session,
        commitment_id: UUID,
        *,
        notification_resolved: bool = False,
    ) -> RecoveryResult:
        """Recover a commitment from at-risk status back to in_progress.

        This handles the recovery flow when the situation has improved:
        1. Updates commitment status to in_progress
        2. Sets CleanupPlan status to cancelled
        3. Optionally marks notification task as skipped if resolved

        Args:
            session: Database session
            commitment_id: ID of commitment to recover
            notification_resolved: If True, mark notification task as skipped

        Returns:
            RecoveryResult with updated entities

        Raises:
            ValueError: If commitment not found or not in at_risk status
        """
        # Get commitment
        commitment = session.get(Commitment, commitment_id)
        if commitment is None:
            msg = f"Commitment {commitment_id} not found"
            raise ValueError(msg)

        # Verify status is at_risk
        if commitment.status != CommitmentStatus.AT_RISK:
            msg = f"Commitment is not at-risk (current status: {commitment.status.value})"
            raise ValueError(msg)

        # Update commitment status
        commitment.status = CommitmentStatus.IN_PROGRESS
        commitment.updated_at = datetime.now(UTC)
        session.add(commitment)

        # Get cleanup plan and cancel it
        cleanup_plan = session.exec(
            select(CleanupPlan).where(CleanupPlan.commitment_id == commitment_id)
        ).first()

        notification_task: Task | None = None
        notification_still_needed = False

        if cleanup_plan:
            cleanup_plan.status = CleanupPlanStatus.CANCELLED
            cleanup_plan.updated_at = datetime.now(UTC)
            session.add(cleanup_plan)

            # Handle notification task
            if cleanup_plan.notification_task_id:
                notification_task = session.get(Task, cleanup_plan.notification_task_id)
                if notification_task and notification_task.status == TaskStatus.PENDING:
                    if notification_resolved:
                        # Mark as skipped with reason
                        notification_task.status = TaskStatus.SKIPPED
                        notification_task.scope = (
                            notification_task.scope or ""
                        ) + "\n\n[Skipped: Situation resolved]"
                        notification_task.updated_at = datetime.now(UTC)
                        session.add(notification_task)
                    else:
                        # User still needs to decide about notification
                        notification_still_needed = True

        session.commit()

        return RecoveryResult(
            commitment=commitment,
            cleanup_plan=cleanup_plan,
            notification_task=notification_task,
            notification_still_needed=notification_still_needed,
        )

    def _generate_notification_scope(
        self,
        commitment: Commitment,
        stakeholder_name: str,
        reason: str,
        impact_description: str | None,
    ) -> str:
        """Generate the notification draft for the task scope."""
        due_date_str = commitment.due_date.strftime("%B %d, %Y")
        impact = impact_description or "Impact to be determined"

        return f"""NOTIFICATION DRAFT:

To: {stakeholder_name}
Re: {commitment.deliverable}

I need to let you know that I may not be able to deliver \
"{commitment.deliverable}" by {due_date_str} as committed.

Reason: {reason}
Impact: {impact}
Proposed resolution: [Please discuss with stakeholder]

---
Mark this task complete after you've sent the notification."""

    def calculate_integrity_metrics(self, session: Session) -> IntegrityMetrics:
        """Calculate integrity metrics from commitment history.

        Args:
            session: Database session

        Returns:
            IntegrityMetrics with calculated values
        """
        # Count completed commitments
        total_completed = session.exec(
            select(func.count())
            .select_from(Commitment)
            .where(Commitment.status == CommitmentStatus.COMPLETED)
        ).one()

        # Count on-time completions
        total_on_time = session.exec(
            select(func.count())
            .select_from(Commitment)
            .where(
                Commitment.status == CommitmentStatus.COMPLETED,
                Commitment.completed_on_time == True,  # noqa: E712
            )
        ).one()

        # Count at-risk commitments (current and historical)
        total_at_risk = session.exec(
            select(func.count())
            .select_from(Commitment)
            .where(
                Commitment.marked_at_risk_at.is_not(None)  # type: ignore[union-attr]
            )
        ).one()

        # Count abandoned commitments
        total_abandoned = session.exec(
            select(func.count())
            .select_from(Commitment)
            .where(Commitment.status == CommitmentStatus.ABANDONED)
        ).one()

        # Calculate on_time_rate
        on_time_rate = 1.0  # Clean slate default
        if total_completed > 0:
            on_time_rate = total_on_time / total_completed

        # Calculate cleanup completion rate
        total_plans = session.exec(select(func.count()).select_from(CleanupPlan)).one()

        completed_plans = session.exec(
            select(func.count())
            .select_from(CleanupPlan)
            .where(CleanupPlan.status == CleanupPlanStatus.COMPLETED)
        ).one()

        cleanup_completion_rate = 1.0  # Clean slate default
        if total_plans > 0:
            cleanup_completion_rate = completed_plans / total_plans

        # Notification timeliness: how early users notify when at-risk
        # 7+ days before due = 1.0, 0 days = 0.0, linear interpolation
        notification_timeliness = self._calculate_notification_timeliness(session)

        # Streak calculation: consecutive weeks with all on-time completions
        current_streak_weeks = self._calculate_streak_weeks(session)

        # Calculate estimation accuracy
        estimation_accuracy, tasks_with_estimates = self._calculate_estimation_accuracy(session)

        return IntegrityMetrics(
            on_time_rate=on_time_rate,
            notification_timeliness=notification_timeliness,
            cleanup_completion_rate=cleanup_completion_rate,
            current_streak_weeks=current_streak_weeks,
            total_completed=total_completed,
            total_on_time=total_on_time,
            total_at_risk=total_at_risk,
            total_abandoned=total_abandoned,
            estimation_accuracy=estimation_accuracy,
            tasks_with_estimates=tasks_with_estimates,
        )

    def detect_risks(self, session: Session) -> RiskSummary:
        """Detect at-risk commitments for proactive alerting.

        Checks for:
        1. Overdue commitments (due_date < today, status pending/in_progress)
        2. Commitments due within 24 hours with status=pending
        3. Stalled in_progress commitments (due within 48h, no task activity in 24h)

        Args:
            session: Database session

        Returns:
            RiskSummary with categorized at-risk commitments
        """
        today = datetime.now(UTC).date()
        now = datetime.now(UTC)
        in_24_hours = today + timedelta(days=1)  # Tomorrow
        in_48_hours = today + timedelta(days=2)  # Day after tomorrow
        hours_24_ago = now - timedelta(hours=HOURS_24)

        # Statuses that can be at-risk
        active_statuses = [CommitmentStatus.PENDING, CommitmentStatus.IN_PROGRESS]

        # 1. Overdue commitments
        overdue = list(
            session.exec(
                select(Commitment).where(
                    Commitment.due_date < today,
                    Commitment.status.in_(active_statuses),  # type: ignore[union-attr]
                )
            ).all()
        )

        # 2. Due within 24 hours and still pending
        due_soon = list(
            session.exec(
                select(Commitment).where(
                    Commitment.due_date >= today,
                    Commitment.due_date <= in_24_hours,
                    Commitment.status == CommitmentStatus.PENDING,
                )
            ).all()
        )

        # 3. Stalled: in_progress, due within 48h, no recent task activity
        # For simplicity, we check commitments in_progress due within 48h
        # A more complete implementation would track task.updated_at
        potentially_stalled = list(
            session.exec(
                select(Commitment).where(
                    Commitment.due_date >= today,
                    Commitment.due_date <= in_48_hours,
                    Commitment.status == CommitmentStatus.IN_PROGRESS,
                )
            ).all()
        )

        # Filter to those with no recent task updates
        # For now, we'll use commitment.updated_at as a proxy
        stalled = []
        for c in potentially_stalled:
            updated = c.updated_at
            # Handle timezone-naive datetimes from SQLite
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=UTC)
            if updated < hours_24_ago:
                stalled.append(c)

        return RiskSummary(
            overdue_commitments=overdue,
            due_soon_commitments=due_soon,
            stalled_commitments=stalled,
        )

    def _calculate_notification_timeliness(self, session: Session) -> float:
        """Calculate average notification timeliness score.

        Measures how early users mark commitments as at-risk before the due date.
        7+ days before due = 1.0, 0 days (on due date) = 0.0, linear interpolation.

        Args:
            session: Database session

        Returns:
            Timeliness score from 0.0 to 1.0, defaults to 1.0 if no at-risk history
        """
        # Get all commitments that were marked at-risk
        at_risk_commitments = session.exec(
            select(Commitment).where(Commitment.marked_at_risk_at.is_not(None))  # type: ignore[union-attr]
        ).all()

        if not at_risk_commitments:
            return 1.0  # Clean slate

        total_score = 0.0
        for commitment in at_risk_commitments:
            if commitment.marked_at_risk_at is None or commitment.due_date is None:
                continue

            # Calculate days before due when marked at-risk
            marked_date = commitment.marked_at_risk_at.date()
            days_before_due = (commitment.due_date - marked_date).days

            # Normalize: 7+ days = 1.0, 0 days = 0.0, negative = 0.0
            if days_before_due >= 7:
                score = 1.0
            elif days_before_due <= 0:
                score = 0.0
            else:
                score = days_before_due / 7.0

            total_score += score

        return total_score / len(at_risk_commitments) if at_risk_commitments else 1.0

    def _calculate_streak_weeks(self, session: Session) -> int:
        """Calculate consecutive weeks with all on-time completions.

        Counts consecutive weeks (starting from current) where all completed
        commitments were on time. Streak resets on late completion or abandonment.

        Args:
            session: Database session

        Returns:
            Number of consecutive on-time weeks, 0 if no history or recent miss
        """
        # Get all completed commitments, ordered by completion date descending
        completed = session.exec(
            select(Commitment)
            .where(
                Commitment.status == CommitmentStatus.COMPLETED,
                Commitment.completed_at.is_not(None),  # type: ignore[union-attr]
            )
            .order_by(Commitment.completed_at.desc())  # type: ignore[union-attr]
        ).all()

        if not completed:
            return 0  # No history

        # Group by ISO week
        weeks_data: dict[tuple[int, int], list[bool]] = {}  # (year, week) -> [on_time...]
        for c in completed:
            if c.completed_at is None:
                continue
            iso_cal = c.completed_at.isocalendar()
            week_key = (iso_cal.year, iso_cal.week)
            if week_key not in weeks_data:
                weeks_data[week_key] = []
            weeks_data[week_key].append(c.completed_on_time is True)

        # Sort weeks newest first
        sorted_weeks = sorted(weeks_data.keys(), reverse=True)

        # Count consecutive perfect weeks
        streak = 0
        for week_key in sorted_weeks:
            on_time_flags = weeks_data[week_key]
            if all(on_time_flags):
                streak += 1
            else:
                break  # Streak broken

        # Also check for abandonments that would reset streak
        # Get most recent abandonment
        recent_abandon = session.exec(
            select(Commitment)
            .where(Commitment.status == CommitmentStatus.ABANDONED)
            .order_by(Commitment.updated_at.desc())  # type: ignore[arg-type]
            .limit(1)
        ).first()

        if recent_abandon and streak > 0:
            # If there's an abandonment within the streak period, reduce streak
            abandon_iso = recent_abandon.updated_at.isocalendar()
            abandon_week = (abandon_iso.year, abandon_iso.week)

            # Check if abandonment is within our streak period
            streak_start_idx = min(streak, len(sorted_weeks))
            if streak_start_idx > 0:
                oldest_streak_week = sorted_weeks[streak_start_idx - 1]
                if abandon_week >= oldest_streak_week:
                    # Abandonment within streak period - count weeks after abandonment
                    new_streak = 0
                    for week_key in sorted_weeks:
                        if week_key <= abandon_week:
                            break
                        if all(weeks_data[week_key]):
                            new_streak += 1
                        else:
                            break
                    streak = new_streak

        return streak

    def _calculate_estimation_accuracy(self, session: Session) -> tuple[float, int]:
        """Calculate estimation accuracy from task history.

        Uses exponential decay weighting: recent tasks count more than older ones.
        Last 7 days = full weight, weight halves every 7 days, max 90 days.

        Accuracy is based on how close actual hours category is to ON_TARGET:
        - ON_TARGET = 1.0 accuracy
        - SHORTER/LONGER = 0.75 accuracy
        - MUCH_SHORTER/MUCH_LONGER = 0.25 accuracy

        Args:
            session: Database session

        Returns:
            Tuple of (accuracy score 0.0-1.0, count of tasks with estimates)
        """
        now = datetime.now(UTC)
        cutoff = now - timedelta(days=ACCURACY_MAX_AGE_DAYS)

        # Get completed task history entries with both estimate and actual
        completed_entries = session.exec(
            select(TaskHistoryEntry).where(
                TaskHistoryEntry.event_type == TaskEventType.COMPLETED,
                TaskHistoryEntry.estimated_hours.is_not(None),  # type: ignore[union-attr]
                TaskHistoryEntry.actual_hours_category.is_not(None),  # type: ignore[union-attr]
                TaskHistoryEntry.created_at >= cutoff,  # type: ignore[operator]
            )
        ).all()

        tasks_with_estimates = len(completed_entries)

        # Not enough history - return default
        if tasks_with_estimates < MIN_TASKS_FOR_ACCURACY:
            return 1.0, tasks_with_estimates

        # Calculate weighted accuracy
        total_weight = 0.0
        weighted_accuracy = 0.0

        for entry in completed_entries:
            if entry.actual_hours_category is None:
                continue

            # Calculate age-based weight with exponential decay
            # At 0 days weight=1.0, at 7 days weight=0.5, at 14 days weight=0.25
            age_days = (now - entry.created_at.replace(tzinfo=UTC)).days
            weight = 2.0 ** (-age_days / ACCURACY_DECAY_DAYS)

            # Calculate accuracy based on category
            # ON_TARGET = 1.0, SHORTER/LONGER = 0.75, MUCH_SHORTER/MUCH_LONGER = 0.25
            multiplier = entry.actual_hours_category.multiplier
            if 0.85 <= multiplier <= 1.15:  # ON_TARGET range
                accuracy = 1.0
            elif 0.5 <= multiplier < 0.85 or 1.15 < multiplier <= 1.5:  # SHORTER/LONGER
                accuracy = 0.75
            else:  # MUCH_SHORTER or MUCH_LONGER
                accuracy = 0.25

            weighted_accuracy += accuracy * weight
            total_weight += weight

        if total_weight == 0:
            return 1.0, tasks_with_estimates

        return weighted_accuracy / total_weight, tasks_with_estimates

    def calculate_integrity_metrics_with_trends(self, session: Session) -> IntegrityMetrics:
        """Calculate integrity metrics including trend indicators.

        Compares current 30-day period with previous 30-day period to
        determine if metrics are improving, declining, or stable.

        Args:
            session: Database session

        Returns:
            IntegrityMetrics with trend fields populated
        """
        # Get current metrics
        current = self.calculate_integrity_metrics(session)

        # Calculate previous period metrics for comparison
        now = datetime.now(UTC)
        cutoff = now - timedelta(days=TREND_PERIOD_DAYS)
        prev_cutoff = cutoff - timedelta(days=TREND_PERIOD_DAYS)

        # Calculate on-time rate for previous period
        prev_on_time_rate = self._calculate_period_on_time_rate(session, prev_cutoff, cutoff)

        # Calculate cleanup rate for previous period
        prev_cleanup_rate = self._calculate_period_cleanup_rate(session, prev_cutoff, cutoff)

        # Calculate notification timeliness for previous period
        prev_notification = self._calculate_period_notification_timeliness(
            session, prev_cutoff, cutoff
        )

        # Determine trends
        on_time_trend = self._determine_trend(prev_on_time_rate, current.on_time_rate)
        notification_trend = self._determine_trend(
            prev_notification, current.notification_timeliness
        )
        cleanup_trend = self._determine_trend(prev_cleanup_rate, current.cleanup_completion_rate)

        # Calculate overall trend from composite score
        prev_composite = (
            prev_on_time_rate * 0.35
            + prev_notification * 0.25
            + prev_cleanup_rate * 0.25
            + current.estimation_accuracy * 0.10  # Use current, no history
            + min(current.current_streak_weeks * 2, 5) / 100
        ) * 100
        overall_trend = self._determine_trend(prev_composite, current.composite_score)

        # Return metrics with trends
        return IntegrityMetrics(
            on_time_rate=current.on_time_rate,
            notification_timeliness=current.notification_timeliness,
            cleanup_completion_rate=current.cleanup_completion_rate,
            current_streak_weeks=current.current_streak_weeks,
            total_completed=current.total_completed,
            total_on_time=current.total_on_time,
            total_at_risk=current.total_at_risk,
            total_abandoned=current.total_abandoned,
            estimation_accuracy=current.estimation_accuracy,
            tasks_with_estimates=current.tasks_with_estimates,
            on_time_trend=on_time_trend,
            notification_trend=notification_trend,
            cleanup_trend=cleanup_trend,
            overall_trend=overall_trend,
        )

    def _determine_trend(self, prev_value: float, curr_value: float) -> TrendDirection:
        """Determine trend direction between two values.

        Args:
            prev_value: Previous period value
            curr_value: Current period value

        Returns:
            TrendDirection indicating if value is improving, declining, or stable
        """
        diff = curr_value - prev_value
        if diff > TREND_THRESHOLD:
            return TrendDirection.UP
        if diff < -TREND_THRESHOLD:
            return TrendDirection.DOWN
        return TrendDirection.STABLE

    def _calculate_period_on_time_rate(
        self, session: Session, start: datetime, end: datetime
    ) -> float:
        """Calculate on-time rate for a specific period.

        Args:
            session: Database session
            start: Period start datetime
            end: Period end datetime

        Returns:
            On-time rate (0.0-1.0), defaults to 1.0 if no data
        """
        # Get completed commitments in period
        period_completed = session.exec(
            select(func.count())
            .select_from(Commitment)
            .where(
                Commitment.status == CommitmentStatus.COMPLETED,
                Commitment.completed_at >= start,  # type: ignore[operator]
                Commitment.completed_at < end,  # type: ignore[operator]
            )
        ).one()

        if period_completed == 0:
            return 1.0  # Clean slate for period

        period_on_time = session.exec(
            select(func.count())
            .select_from(Commitment)
            .where(
                Commitment.status == CommitmentStatus.COMPLETED,
                Commitment.completed_at >= start,  # type: ignore[operator]
                Commitment.completed_at < end,  # type: ignore[operator]
                Commitment.completed_on_time == True,  # noqa: E712
            )
        ).one()

        return period_on_time / period_completed

    def _calculate_period_cleanup_rate(
        self, session: Session, start: datetime, end: datetime
    ) -> float:
        """Calculate cleanup completion rate for a specific period.

        Args:
            session: Database session
            start: Period start datetime
            end: Period end datetime

        Returns:
            Cleanup rate (0.0-1.0), defaults to 1.0 if no data
        """
        period_plans = session.exec(
            select(func.count())
            .select_from(CleanupPlan)
            .where(
                CleanupPlan.created_at >= start,  # type: ignore[operator]
                CleanupPlan.created_at < end,  # type: ignore[operator]
            )
        ).one()

        if period_plans == 0:
            return 1.0  # Clean slate for period

        period_completed = session.exec(
            select(func.count())
            .select_from(CleanupPlan)
            .where(
                CleanupPlan.status == CleanupPlanStatus.COMPLETED,
                CleanupPlan.created_at >= start,  # type: ignore[operator]
                CleanupPlan.created_at < end,  # type: ignore[operator]
            )
        ).one()

        return period_completed / period_plans

    def _calculate_period_notification_timeliness(
        self, session: Session, start: datetime, end: datetime
    ) -> float:
        """Calculate notification timeliness for a specific period.

        Args:
            session: Database session
            start: Period start datetime
            end: Period end datetime

        Returns:
            Timeliness score (0.0-1.0), defaults to 1.0 if no data
        """
        # Get commitments marked at-risk in period
        at_risk_in_period = session.exec(
            select(Commitment).where(
                Commitment.marked_at_risk_at.is_not(None),  # type: ignore[union-attr]
                Commitment.marked_at_risk_at >= start,  # type: ignore[operator]
                Commitment.marked_at_risk_at < end,  # type: ignore[operator]
            )
        ).all()

        if not at_risk_in_period:
            return 1.0  # Clean slate for period

        total_score = 0.0
        for commitment in at_risk_in_period:
            if commitment.marked_at_risk_at is None or commitment.due_date is None:
                continue

            marked_date = commitment.marked_at_risk_at.date()
            days_before_due = (commitment.due_date - marked_date).days

            if days_before_due >= 7:
                score = 1.0
            elif days_before_due <= 0:
                score = 0.0
            else:
                score = days_before_due / 7.0

            total_score += score

        return total_score / len(at_risk_in_period) if at_risk_in_period else 1.0

    def get_affecting_commitments(self, session: Session) -> list[AffectingCommitment]:
        """Get recent commitments that negatively affected the integrity score.

        Returns commitments from the last 30 days where:
        - completed_on_time = False (late completion)
        - status = abandoned

        Args:
            session: Database session

        Returns:
            List of AffectingCommitment with reason for each
        """
        now = datetime.now(UTC)
        cutoff = now - timedelta(days=AFFECTING_SCORE_DAYS)

        # Get late completions
        late_completions = session.exec(
            select(Commitment)
            .where(
                Commitment.status == CommitmentStatus.COMPLETED,
                Commitment.completed_on_time == False,  # noqa: E712
                Commitment.completed_at >= cutoff,  # type: ignore[operator]
            )
            .order_by(Commitment.completed_at.desc())  # type: ignore[union-attr]
            .limit(MAX_AFFECTING_COMMITMENTS)
        ).all()

        result: list[AffectingCommitment] = [
            AffectingCommitment(commitment=c, reason="completed late") for c in late_completions
        ]

        # Get abandoned commitments
        remaining_slots = MAX_AFFECTING_COMMITMENTS - len(result)
        if remaining_slots > 0:
            abandoned = session.exec(
                select(Commitment)
                .where(
                    Commitment.status == CommitmentStatus.ABANDONED,
                    Commitment.updated_at >= cutoff,  # type: ignore[operator]
                )
                .order_by(Commitment.updated_at.desc())  # type: ignore[arg-type]
                .limit(remaining_slots)
            ).all()

            result.extend(AffectingCommitment(commitment=c, reason="abandoned") for c in abandoned)

        return result
