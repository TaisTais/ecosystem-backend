from typing import Optional, List


def normalize_tags(tags: Optional[List[str]]) -> Optional[str]:
    """Нормализует список тегов в строку для хранения в БД"""
    if not tags:
        return None

    # Приводим к нижнему регистру, убираем пробелы, удаляем дубли
    normalized = set(tag.strip().lower() for tag in tags if tag and tag.strip())
    return ",".join(sorted(normalized)) if normalized else None