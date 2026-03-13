import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas import SdeTypeItem, UnifiedTreeNode
from app.core.errors import api_error
from app.database import get_db
from app.schemas import ErrorResponse, ValidationErrorResponse


router = APIRouter(prefix="/api/v1/sde", tags=["Static Data Export"])
logger = logging.getLogger(__name__)

SDE_SCHEMA = "sde"
UNIFIED_MARKET_TREE_VIEW_CANDIDATES = ("vw_unified_market_tree",)
TYPE_TABLE_CANDIDATES = ("types",)


def _quote_identifier(identifier: str) -> str:
    escaped = identifier.replace('"', '""')
    return f'"{escaped}"'


def _pick_column(columns: dict[str, str], *candidates: str) -> str | None:
    for candidate in candidates:
        resolved = columns.get(candidate.lower())
        if resolved:
            return resolved
    return None


def _build_name_expr(columns: dict[str, str], candidates: list[str], *, fallback_expr: str) -> str:
    parts = [_quote_identifier(columns[candidate.lower()]) for candidate in candidates if candidate.lower() in columns]
    if not parts:
        return fallback_expr
    if len(parts) == 1:
        return parts[0]
    return f"COALESCE({', '.join(parts)})"


async def _get_table_columns(db: AsyncSession, table_name: str) -> tuple[dict[str, str], dict[str, str]]:
    stmt = text(
        """
        SELECT column_name, data_type, udt_name
        FROM information_schema.columns
        WHERE table_schema = :schema AND table_name = :table_name
        ORDER BY ordinal_position
        """
    )
    result = await db.execute(stmt, {"schema": SDE_SCHEMA, "table_name": table_name})
    rows = result.fetchall()
    columns = {row[0].lower(): row[0] for row in rows}
    column_types = {row[0].lower(): str(row[1] or row[2] or "").lower() for row in rows}
    return columns, column_types


async def _resolve_table_columns(db: AsyncSession, table_names: tuple[str, ...]) -> tuple[str, dict[str, str], dict[str, str]]:
    for table_name in table_names:
        columns, column_types = await _get_table_columns(db, table_name)
        if columns:
            return table_name, columns, column_types

    if len(table_names) == 1:
        suffix = f"{SDE_SCHEMA}.{table_names[0]}"
    else:
        suffix = " 或 ".join(f"{SDE_SCHEMA}.{table_name}" for table_name in table_names)
    raise api_error(503, "sde_table_missing", f"当前数据库未导入 {suffix} 表或视图")


def _build_truthy_filter(column_name: str | None, column_types: dict[str, str]) -> str:
    if not column_name:
        return ""

    column_type = column_types.get(column_name.lower(), "")
    quoted_column = _quote_identifier(column_name)

    if column_type in {"boolean", "bool"}:
        return f"AND {quoted_column} = TRUE"

    if column_type in {"smallint", "integer", "bigint", "int2", "int4", "int8", "numeric", "decimal", "real", "double precision", "float4", "float8"}:
        return f"AND COALESCE({quoted_column}, 0) <> 0"

    return f"AND {quoted_column} IS NOT NULL"


def _sort_tree(nodes: list[dict]) -> None:
    nodes.sort(key=lambda item: item["name"])
    for node in nodes:
        if node["children"]:
            _sort_tree(node["children"])


@router.get(
    "/market-groups/tree",
    response_model=list[UnifiedTreeNode],
    summary="获取统一市场分类树",
    description="直接读取统一市场树视图，并装配为前端树节点结构。",
    responses={
        200: {"description": "成功返回市场分类树"},
        503: {"description": "当前数据库未导入 SDE 静态数据", "model": ErrorResponse},
    },
)
async def get_market_group_tree(db: AsyncSession = Depends(get_db)):
    try:
        table_name, columns, _column_types = await _resolve_table_columns(db, UNIFIED_MARKET_TREE_VIEW_CANDIDATES)

        key_column = _pick_column(columns, "key")
        parent_key_column = _pick_column(columns, "parent_key")
        name_column = _pick_column(columns, "name")
        icon_column = _pick_column(columns, "iconname", "icon_name")
        is_group_column = _pick_column(columns, "is_group")
        type_id_column = _pick_column(columns, "type_id")
        level_column = _pick_column(columns, "level")

        if not key_column or not name_column or not is_group_column:
            raise api_error(503, "sde_table_shape_invalid", f"sde.{table_name} 缺少必要的 key/name/is_group 字段")

        key_expr = f"CAST({_quote_identifier(key_column)} AS TEXT)"
        parent_expr = f"CAST({_quote_identifier(parent_key_column)} AS TEXT)" if parent_key_column else "NULL"

        icon_expr = _quote_identifier(icon_column) if icon_column else "NULL"
        is_group_expr = _quote_identifier(is_group_column) if is_group_column else "TRUE"
        type_expr = _quote_identifier(type_id_column) if type_id_column else "NULL"
        level_expr = _quote_identifier(level_column) if level_column else "0"

        stmt = text(
            f"""
            SELECT
                {key_expr} AS key,
                {parent_expr} AS parent_key,
                {_quote_identifier(name_column)} AS name,
                {icon_expr} AS iconname,
                {is_group_expr} AS is_group,
                {type_expr} AS type_id,
                {level_expr} AS level
            FROM {SDE_SCHEMA}.{_quote_identifier(table_name)}
            ORDER BY 7 ASC, 3 ASC, 1 ASC
            """
        )
        result = await db.execute(stmt)
        rows = result.mappings().all()
    except SQLAlchemyError as exc:
        logger.exception("💥 [SDE] 从 SDE 加载统一市场树失败")
        raise api_error(503, "sde_query_failed", "市场分类静态数据读取失败，请确认 SDE 数据已正确导入") from exc

    node_dict: dict[str, dict] = {}
    tree: list[dict] = []
    parent_lookup: dict[str, str | None] = {}

    for row in rows:
        key = str(row["key"])
        raw_parent_key = row["parent_key"]
        parent_key = str(raw_parent_key) if raw_parent_key is not None and str(raw_parent_key).strip() not in {"", "0"} else None
        node_dict[key] = {
            "key": key,
            "parent_key": parent_key,
            "name": str(row["name"] or key),
            "iconname": row["iconname"],
            "is_group": bool(row["is_group"]),
            "type_id": int(row["type_id"]) if row["type_id"] is not None else None,
            "children": [],
        }
        parent_lookup[key] = parent_key

    for key, node in node_dict.items():
        parent_key = parent_lookup[key]
        if parent_key is not None and parent_key in node_dict:
            node_dict[parent_key]["children"].append(node)
        else:
            tree.append(node)

    _sort_tree(tree)
    return tree


@router.get(
    "/types",
    response_model=list[SdeTypeItem],
    summary="根据市场分类获取物品列表",
    description="读取指定 market_group_id 下已发布的市场物品。",
    responses={
        200: {"description": "成功返回该分类下的物品列表"},
        422: {"description": "group_id 缺失或格式非法", "model": ValidationErrorResponse},
        503: {"description": "当前数据库未导入 SDE 静态数据", "model": ErrorResponse},
    },
)
async def get_types_by_group(
    group_id: int = Query(..., ge=1, description="市场分类 ID。"),
    db: AsyncSession = Depends(get_db),
):
    try:
        table_name, columns, column_types = await _resolve_table_columns(db, TYPE_TABLE_CANDIDATES)
        type_id_column = _pick_column(columns, "type_id", "typeid")
        group_column = _pick_column(columns, "market_group_id", "marketgroupid")
        volume_column = _pick_column(columns, "volume")
        published_column = _pick_column(columns, "published")
        name_expr = _build_name_expr(
            columns,
            ["zh_name", "name", "type_name", "typename", "en_name", "de_name"],
            fallback_expr="'<unknown type>'",
        )

        if not type_id_column or not group_column:
            raise api_error(503, "sde_table_shape_invalid", "sde.types 缺少必要的类型或分类字段")

        published_filter = _build_truthy_filter(published_column, column_types)
        volume_expr = _quote_identifier(volume_column) if volume_column else "NULL"
        stmt = text(
            f"""
            SELECT
                {_quote_identifier(type_id_column)} AS type_id,
                {name_expr} AS name,
                {volume_expr} AS volume,
                {_quote_identifier(group_column)} AS market_group_id
            FROM {SDE_SCHEMA}.{_quote_identifier(table_name)}
            WHERE {_quote_identifier(group_column)} = :group_id
                {published_filter}
            ORDER BY 2 ASC, 1 ASC
            """
        )
        result = await db.execute(stmt, {"group_id": group_id})
        return [dict(row) for row in result.mappings().all()]
    except SQLAlchemyError as exc:
        logger.exception("💥 [SDE] 按分组加载 SDE 物品失败：分组 ID=%s", group_id)
        raise api_error(503, "sde_query_failed", "市场物品静态数据读取失败，请确认 SDE 数据已正确导入") from exc


@router.get(
    "/types/search",
    response_model=list[SdeTypeItem],
    summary="按名称模糊搜索市场物品",
    description="按物品名称进行模糊搜索，默认限制返回前 50 条已发布且存在市场分类的物品。",
    responses={
        200: {"description": "成功返回物品搜索结果"},
        422: {"description": "name 缺失、为空或过长", "model": ValidationErrorResponse},
        503: {"description": "当前数据库未导入 SDE 静态数据", "model": ErrorResponse},
    },
)
async def search_types_by_name(
    name: str = Query(..., min_length=1, max_length=100, description="搜索关键字。"),
    db: AsyncSession = Depends(get_db),
):
    keyword = name.strip()
    if not keyword:
        raise api_error(422, "validation_error", "搜索关键字不能为空")

    try:
        table_name, columns, column_types = await _resolve_table_columns(db, TYPE_TABLE_CANDIDATES)
        type_id_column = _pick_column(columns, "type_id", "typeid")
        group_column = _pick_column(columns, "market_group_id", "marketgroupid")
        volume_column = _pick_column(columns, "volume")
        published_column = _pick_column(columns, "published")
        name_expr = _build_name_expr(
            columns,
            ["zh_name", "name", "type_name", "typename", "en_name", "de_name"],
            fallback_expr="'<unknown type>'",
        )

        if not type_id_column or not group_column:
            raise api_error(503, "sde_table_shape_invalid", "sde.types 缺少必要的类型或分类字段")

        published_filter = _build_truthy_filter(published_column, column_types)
        volume_expr = _quote_identifier(volume_column) if volume_column else "NULL"
        stmt = text(
            f"""
            SELECT
                {_quote_identifier(type_id_column)} AS type_id,
                {name_expr} AS name,
                {volume_expr} AS volume,
                {_quote_identifier(group_column)} AS market_group_id
            FROM {SDE_SCHEMA}.{_quote_identifier(table_name)}
            WHERE {name_expr} ILIKE :name
                AND {_quote_identifier(group_column)} IS NOT NULL
                {published_filter}
            ORDER BY 2 ASC, 1 ASC
            LIMIT 50
            """
        )
        result = await db.execute(stmt, {"name": f"%{keyword}%"})
        return [dict(row) for row in result.mappings().all()]
    except SQLAlchemyError as exc:
        logger.exception("💥 [SDE] 搜索 SDE 物品失败：关键字=%s", keyword)
        raise api_error(503, "sde_query_failed", "市场物品搜索失败，请确认 SDE 数据已正确导入") from exc