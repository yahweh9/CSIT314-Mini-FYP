# controllers/CategoryController.py
from __future__ import annotations

from typing import Tuple, List, Dict, Optional
from sqlalchemy import func
from entities.UserEntity import db
from entities.VolunteerServiceCategoryEntity import VolunteerServiceCategoryEntity as VCat
from entities.PINRequestEntity import PINRequestEntity

# Statuses treated as "active/linked" for delete guard
_ACTIVE_STATUSES = {"pending", "active", "late"}

class CategoryController:
    # ---------- Queries / Lists ----------

    @staticmethod
    def list_categories() -> List[VCat]:
        """Return all categories ordered by name."""
        return VCat.query.order_by(VCat.name.asc()).all()

    @staticmethod
    def list_with_counts() -> Tuple[List[VCat], Dict[Optional[int], int]]:
        """
        Returns:
            (cats, counts)
            cats   -> list[VCat] ordered by name
            counts -> dict[category_id -> int], includes {None: unassigned_count}
        """
        # rows: [(VCat, count), ...] including categories with zero linked requests
        rows = (
            db.session.query(VCat, func.count(PINRequestEntity.request_id))
            .outerjoin(
                PINRequestEntity,
                PINRequestEntity.volunteer_service_category_id == VCat.id
            )
            .group_by(VCat.id)
            .order_by(VCat.name.asc())
            .all()
        )

        cats: List[VCat] = [c for (c, _) in rows]
        counts: Dict[Optional[int], int] = {c.id: int(cnt or 0) for (c, cnt) in rows}

        # Include "Unassigned" bucket (requests with NULL category)
        unassigned = (
            db.session.query(func.count(PINRequestEntity.request_id))
            .filter(PINRequestEntity.volunteer_service_category_id.is_(None))
            .scalar()
        )
        counts[None] = int(unassigned or 0)

        return cats, counts

    # ---------- Validation helpers ----------

    @staticmethod
    def _name_exists(name: str, exclude_id: int | None = None) -> bool:
        """Case-insensitive uniqueness check."""
        q = VCat.query.filter(func.lower(VCat.name) == func.lower(name.strip()))
        if exclude_id:
            q = q.filter(VCat.id != exclude_id)
        return db.session.query(q.exists()).scalar()

    # ---------- A08.1: Add new category ----------

    @staticmethod
    def create_category(name: str, description: str | None, is_active: bool) -> Tuple[bool, str]:
        if not name or not name.strip():
            return False, "Category name is required."
        if CategoryController._name_exists(name):
            # A08.E1
            return False, "Category name already exists."

        try:
            cat = VCat(name=name.strip(), description=(description or "").strip(), is_active=bool(is_active))
            db.session.add(cat)
            db.session.commit()
            return True, f"Created category '{cat.name}'."
        except Exception as e:
            # A08.E3
            db.session.rollback()
            return False, f"System error creating category: {e!s}"

    # ---------- A08.2: Edit category ----------

    @staticmethod
    def update_category(cat_id: int, name: str, description: str | None, is_active: bool) -> Tuple[bool, str]:
        cat = VCat.query.get(cat_id)
        if not cat:
            return False, "Category not found."

        if not name or not name.strip():
            return False, "Category name is required."

        if CategoryController._name_exists(name, exclude_id=cat_id):
            # A08.E1
            return False, "Category name already exists."

        try:
            cat.name = name.strip()
            cat.description = (description or "").strip()
            cat.is_active = bool(is_active)
            db.session.commit()
            return True, f"Updated category '{cat.name}'."
        except Exception as e:
            # A08.E3
            db.session.rollback()
            return False, f"System error updating category: {e!s}"

    # ---------- A08.3: Delete category (guard for active links) ----------

    @staticmethod
    def delete_category(cat_id: int) -> Tuple[bool, str]:
        cat = VCat.query.get(cat_id)
        if not cat:
            return False, "Category not found."

        # A08.E2: block if linked to active requests
        linked_active = (
            PINRequestEntity.query
            .filter(
                PINRequestEntity.volunteer_service_category_id == cat_id,
                PINRequestEntity.status.in_(_ACTIVE_STATUSES),
            )
            .count()
        )
        if linked_active > 0:
            return False, f"Cannot delete: {linked_active} active request(s) are using this category."

        try:
            db.session.delete(cat)
            db.session.commit()
            return True, f"Deleted category '{cat.name}'."
        except Exception as e:
            # A08.E3
            db.session.rollback()
            return False, f"System error deleting category: {e!s}"

    # ---------- Optional: counts breakdown by status for a set of IDs ----------

    @staticmethod
    def counts_for(cat_ids: list[int]) -> Dict[int, Dict[str, int]]:
        """
        Returns {cat_id: {'pending': n, 'active': n, 'late': n, 'completed': n, 'total': n}}
        """
        out: Dict[int, Dict[str, int]] = {
            cid: {'pending': 0, 'active': 0, 'late': 0, 'completed': 0, 'total': 0}
            for cid in cat_ids
        }
        if not cat_ids:
            return out

        rows = (
            db.session.query(
                PINRequestEntity.volunteer_service_category_id,
                PINRequestEntity.status,
                func.count().label("cnt"),
            )
            .filter(PINRequestEntity.volunteer_service_category_id.in_(cat_ids))
            .group_by(PINRequestEntity.volunteer_service_category_id, PINRequestEntity.status)
            .all()
        )
        for cid, status, cnt in rows:
            if cid in out:
                key = (status or "unknown").lower()
                if key not in out[cid]:
                    out[cid][key] = 0
                out[cid][key] += int(cnt or 0)
                out[cid]['total'] += int(cnt or 0)
        return out
