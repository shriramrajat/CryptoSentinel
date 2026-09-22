"""
Migration Lifecycle State Machine and Roadmap Generator for CryptoSentinel Phase 3.

Manages migration lifecycle states (DISCOVERED -> ASSESSED -> PLANNED -> READY -> IN_PROGRESS -> MIGRATED -> VERIFIED)
with strict transition validation and step-by-step roadmap action item generation.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional

from ecdat.models import CryptoAsset
from ecdat.pqc_recommendation import MigrationRecommendation


class LifecycleState(str, Enum):
    """Migration lifecycle state enumeration."""
    DISCOVERED = "DISCOVERED"
    ASSESSED = "ASSESSED"
    PLANNED = "PLANNED"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    MIGRATED = "MIGRATED"
    VERIFIED = "VERIFIED"


VALID_TRANSITIONS: Dict[LifecycleState, List[LifecycleState]] = {
    LifecycleState.DISCOVERED: [LifecycleState.ASSESSED, LifecycleState.DISCOVERED],
    LifecycleState.ASSESSED: [LifecycleState.PLANNED, LifecycleState.DISCOVERED],
    LifecycleState.PLANNED: [LifecycleState.READY, LifecycleState.ASSESSED, LifecycleState.DISCOVERED],
    LifecycleState.READY: [LifecycleState.IN_PROGRESS, LifecycleState.PLANNED, LifecycleState.DISCOVERED],
    LifecycleState.IN_PROGRESS: [LifecycleState.MIGRATED, LifecycleState.READY, LifecycleState.DISCOVERED],
    LifecycleState.MIGRATED: [LifecycleState.VERIFIED, LifecycleState.IN_PROGRESS, LifecycleState.DISCOVERED],
    LifecycleState.VERIFIED: [LifecycleState.DISCOVERED],
}


@dataclass(frozen=True)
class RoadmapStep:
    """Actionable step in a migration roadmap."""
    step_number: int
    title: str
    description: str
    estimated_effort: str  # "Low", "Medium", "High"
    completed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MigrationRecord:
    """Active migration lifecycle tracking record for an asset."""
    asset_id: str
    current_state: LifecycleState
    last_updated: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    history: List[Dict[str, Any]] = field(default_factory=list)
    notes: Optional[str] = None

    def transition_to(self, new_state: LifecycleState, actor: str = "user", notes: Optional[str] = None) -> bool:
        """Attempts to transition state; raises ValueError if transition is invalid."""
        allowed = VALID_TRANSITIONS.get(self.current_state, [LifecycleState.DISCOVERED])
        if new_state not in allowed:
            raise ValueError(f"Invalid migration state transition: '{self.current_state.value}' -> '{new_state.value}'. Transition sequence must follow DISCOVERED -> ASSESSED -> PLANNED -> READY -> IN_PROGRESS -> MIGRATED -> VERIFIED.")

        timestamp = datetime.now(timezone.utc).isoformat()
        self.history.append({
            "from_state": self.current_state.value,
            "to_state": new_state.value,
            "timestamp": timestamp,
            "actor": actor,
            "notes": notes,
        })
        self.current_state = new_state
        self.last_updated = timestamp
        if notes:
            self.notes = notes
        return True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "current_state": self.current_state.value,
            "last_updated": self.last_updated,
            "history": self.history,
            "notes": self.notes,
        }


def generate_migration_roadmap(
    asset: CryptoAsset,
    recommendation: MigrationRecommendation,
    current_state: LifecycleState = LifecycleState.DISCOVERED,
) -> List[RoadmapStep]:
    """Generates a structured, step-by-step migration roadmap."""
    steps: List[RoadmapStep] = []
    target = recommendation.recommended_algorithm
    m_type = recommendation.migration_type.value

    # Step 1: Discovery & Assessment (Always completed if roadmap is generated)
    steps.append(RoadmapStep(
        step_number=1,
        title="Asset Discovery & Risk Assessment",
        description=f"Identify {asset.algorithm} asset in {asset.file_path}:{asset.line_number} and evaluate quantum/HNDL risk.",
        estimated_effort="Low",
        completed=True,
    ))

    # Step 2: Library & Dependency Preparation
    steps.append(RoadmapStep(
        step_number=2,
        title="Library & Dependency Verification",
        description=f"Verify {asset.language.upper()} library '{asset.library}' support or liboqs bindings for {target}.",
        estimated_effort="Medium",
        completed=current_state in (LifecycleState.PLANNED, LifecycleState.READY, LifecycleState.IN_PROGRESS, LifecycleState.MIGRATED, LifecycleState.VERIFIED),
    ))

    # Step 3: Protocol & Packet Size Impact Analysis
    steps.append(RoadmapStep(
        step_number=3,
        title="Protocol Impact & Buffer Analysis",
        description=f"Evaluate key/signature overhead ({recommendation.constraints.deployment_complexity} complexity) and network MTU fragmentation risk.",
        estimated_effort="Medium",
        completed=current_state in (LifecycleState.READY, LifecycleState.IN_PROGRESS, LifecycleState.MIGRATED, LifecycleState.VERIFIED),
    ))

    # Step 4: Implementation (Direct or Hybrid)
    steps.append(RoadmapStep(
        step_number=4,
        title=f"Implement {m_type} Migration Strategy",
        description=f"Refactor code callsite to use {target} ({recommendation.nist_standard})" +
                    (f" via dual {recommendation.hybrid_strategy.classical_component} + {recommendation.hybrid_strategy.pqc_component} hybrid construction." if recommendation.hybrid_strategy else "."),
        estimated_effort="High",
        completed=current_state in (LifecycleState.IN_PROGRESS, LifecycleState.MIGRATED, LifecycleState.VERIFIED),
    ))

    # Step 5: Test Execution & Interoperability Validation
    steps.append(RoadmapStep(
        step_number=5,
        title="Compatibility & Performance Testing",
        description=f"Execute unit, integration, and performance benchmarks for {target} under load.",
        estimated_effort="Medium",
        completed=current_state in (LifecycleState.MIGRATED, LifecycleState.VERIFIED),
    ))

    # Step 6: Final Deployment & Verification
    steps.append(RoadmapStep(
        step_number=6,
        title="Deploy & Verify Post-Quantum Security",
        description=f"Deploy migrated PQC configuration to production and confirm zero classical quantum vulnerability remaining.",
        estimated_effort="Medium",
        completed=current_state == LifecycleState.VERIFIED,
    ))

    return steps
