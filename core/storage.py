"""数据存储模块：用户画像、关系状态、反馈数据的持久化。"""

import json
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from .user_profile import UserProfile, UserProfileManager, StyleParams, ContactType
from .relationship_state import RelationshipState, RelationshipStateManager, RelationshipStage


class DataStorage:
    """数据存储管理器：处理所有数据的加载、保存与持久化。"""

    def __init__(self, data_dir: str = "data"):
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)
        
        # 定义各类数据的存储路径
        self._profiles_file = self._data_dir / "profiles.json"
        self._states_file = self._data_dir / "relationship_states.json"
        
        logging.info(f"Data directory: {self._data_dir}")

    # ========== 用户画像存储 ==========

    def save_profiles(self, manager: UserProfileManager) -> None:
        """保存所有用户画像到文件。"""
        data = {}
        existing_data = {}
        if self._profiles_file.exists():
            try:
                existing_data = json.loads(self._profiles_file.read_text(encoding='utf-8'))
            except Exception:
                existing_data = {}
        for contact_id, profile in manager.list_profiles().items():
            existing = existing_data.get(contact_id, {})
            description = profile.description or existing.get("description", "")
            contact_name = profile.contact_name or existing.get("contact_name", profile.contact_id)
            record = {
                "contact_id": profile.contact_id,
                "contact_name": contact_name,
                "contact_type": profile.contact_type.value,
                "style_params": {
                    "formality": profile.style_params.formality,
                    "initiative": profile.style_params.initiative,
                    "emotion": profile.style_params.emotion,
                    "humor": profile.style_params.humor,
                    "verbosity": profile.style_params.verbosity,
                },
                "total_messages": profile.total_messages,
                "last_interaction": profile.last_interaction,
                "created_at": profile.created_at,
                "description": description,
            }
            for key in [
                "relationship_type",
                "relative_role",
                "age_group",
                "goals",
                "style_tags",
                "notes",
                "avatar_path",
            ]:
                if key in existing:
                    record[key] = existing[key]
            data[contact_id] = record
        
        self._profiles_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        logging.info(f"Saved {len(data)} profiles to {self._profiles_file}")

    def load_profiles(self, manager: UserProfileManager) -> None:
        """从文件加载用户画像。"""
        if not self._profiles_file.exists():
            logging.info("No existing profiles file found")
            return
        
        data = json.loads(self._profiles_file.read_text(encoding='utf-8'))
        for contact_id, profile_data in data.items():
            style_params = StyleParams(
                formality=profile_data["style_params"]["formality"],
                initiative=profile_data["style_params"]["initiative"],
                emotion=profile_data["style_params"]["emotion"],
                humor=profile_data["style_params"]["humor"],
                verbosity=profile_data["style_params"]["verbosity"],
            )
            
            profile = UserProfile(
                contact_id=profile_data["contact_id"],
                contact_name=profile_data["contact_name"],
                contact_type=ContactType(profile_data["contact_type"]),
                style_params=style_params,
                total_messages=profile_data.get("total_messages", 0),
                last_interaction=profile_data.get("last_interaction"),
                created_at=profile_data.get("created_at", datetime.now().isoformat()),
                description=profile_data.get("description", ""),
            )
            manager._profiles[contact_id] = profile
        
        logging.info(f"Loaded {len(data)} profiles from {self._profiles_file}")

    # ========== 关系状态存储 ==========

    def save_relationship_states(self, manager: RelationshipStateManager) -> None:
        """保存所有关系状态到文件。"""
        data = {}
        for contact_id, state in manager.list_states().items():
            data[contact_id] = {
                "contact_id": state.contact_id,
                "current_stage": state.current_stage.value,
                "interaction_count": state.interaction_count,
                "days_since_interaction": state.days_since_interaction,
                "stage_history": state.stage_history,
                "closeness": state.closeness,
                "trust_level": state.trust_level,
                "interaction_frequency": state.interaction_frequency,
                "updated_at": state.updated_at,
            }
        
        self._states_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        logging.info(f"Saved {len(data)} relationship states to {self._states_file}")

    def load_relationship_states(self, manager: RelationshipStateManager) -> None:
        """从文件加载关系状态。"""
        if not self._states_file.exists():
            logging.info("No existing relationship states file found")
            return
        
        data = json.loads(self._states_file.read_text(encoding='utf-8'))
        for contact_id, state_data in data.items():
            state = RelationshipState(
                contact_id=state_data["contact_id"],
                current_stage=RelationshipStage(state_data["current_stage"]),
                interaction_count=state_data.get("interaction_count", 0),
                days_since_interaction=state_data.get("days_since_interaction", 0),
                stage_history=state_data.get("stage_history", {}),
                closeness=state_data.get("closeness", 0.0),
                trust_level=state_data.get("trust_level", 0.5),
                interaction_frequency=state_data.get("interaction_frequency", 0.0),
                updated_at=state_data.get("updated_at", datetime.now().isoformat()),
            )
            manager._states[contact_id] = state
        
        logging.info(f"Loaded {len(data)} relationship states from {self._states_file}")

    # ========== 统一数据管理 ==========

    def save_all(
        self,
        profile_manager: UserProfileManager,
        state_manager: RelationshipStateManager,
    ) -> None:
        """保存所有数据。"""
        self.save_profiles(profile_manager)
        self.save_relationship_states(state_manager)
        logging.info("All data saved successfully")

    def load_all(
        self,
        profile_manager: UserProfileManager,
        state_manager: RelationshipStateManager,
    ) -> None:
        """加载所有数据。"""
        self.load_profiles(profile_manager)
        self.load_relationship_states(state_manager)
        logging.info("All data loaded successfully")

    def export_profile_summary(self, manager: UserProfileManager, output_file: Optional[str] = None) -> str:
        """导出用户画像摘要报告。"""
        output_file = output_file or str(self._data_dir / "profile_summary.json")
        
        summary = {}
        for contact_id, profile in manager.list_profiles().items():
            summary[contact_id] = {
                "name": profile.contact_name,
                "type": profile.contact_type.value,
                "style": {
                    "formality": f"{profile.style_params.formality:.1%}",
                    "initiative": f"{profile.style_params.initiative:.1%}",
                    "emotion": f"{profile.style_params.emotion:.1%}",
                    "humor": f"{profile.style_params.humor:.1%}",
                    "verbosity": f"{profile.style_params.verbosity:.1%}",
                },
                "statistics": {
                    "total_messages": profile.total_messages,
                    "last_interaction": profile.last_interaction,
                    "created_at": profile.created_at,
                },
            }
        
        Path(output_file).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        logging.info(f"Profile summary exported to {output_file}")
        return output_file

    def export_relationship_summary(self, manager: RelationshipStateManager, output_file: Optional[str] = None) -> str:
        """导出关系状态摘要报告。"""
        output_file = output_file or str(self._data_dir / "relationship_summary.json")
        
        summary = {}
        for contact_id, state in manager.list_states().items():
            summary[contact_id] = {
                "current_stage": state.current_stage.value,
                "metrics": {
                    "closeness": f"{state.closeness:.1%}",
                    "trust_level": f"{state.trust_level:.1%}",
                    "interaction_frequency": f"{state.interaction_frequency:.1%}",
                },
                "statistics": {
                    "interaction_count": state.interaction_count,
                    "days_since_interaction": state.days_since_interaction,
                    "updated_at": state.updated_at,
                },
            }
        
        Path(output_file).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        logging.info(f"Relationship summary exported to {output_file}")
        return output_file
