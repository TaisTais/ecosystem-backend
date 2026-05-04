from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models.achievements import Achievement, ActionType


async def create_default_achievements(session: AsyncSession):
    """Создаёт базовый набор достижений при первом запуске"""

    result = await session.execute(select(Achievement).limit(1))
    if result.scalar_one_or_none():
        print("✅ Достижения уже существуют в базе")
        return

    achievements = [

        # === ЕДИНИЧНЫЕ ДОСТИЖЕНИЯ ===

        Achievement(
            name="Статус добавлен!",
            description="Спасибо, что поддерживаете актуальность карты",
            icon="first_status.png",
            points_reward=5,
            action_type=ActionType.SET_STATUS,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name="Отзыв опубликован!",
            description="Благодарим за обратную связь, вместе делаем карту лучше",
            icon="first_review.png",
            points_reward=10,
            action_type=ActionType.WRITE_REVIEW,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name='На шаг ближе к zero waste!',
            description="Поход со своей тарой зарегистрирован, спасибо, что способствуете сокращению отходов!",
            icon="first_review.png",
            points_reward=15,
            action_type=ActionType.VISIT_OWN_TARA_POINT,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name='Разделяй и утилизируй!',
            description="Сдача вторсырья зарегистрирована, благодарим за осознанную утилизацию!",
            icon="first_review.png",
            points_reward=20,
            action_type=ActionType.VISIT_RECYCLING_POINT,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name="Ваша точка добавлена!",
            description="Благодаря вам карта города стала ещё шире и доступнее",
            icon="first_point.png",
            points_reward=30,
            action_type=ActionType.ADD_POINT,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name='Вместе мы сила!',
            description="Участие в мероприятии подтверждено, спасибо за ваш вклад!",
            icon="first_review.png",
            points_reward=30,
            action_type=ActionType.PARTICIPATE_EVENT,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name='Объединяя город!',
            description="Вы успешно провели мероприятие, благодаря вашему труду город стал лучше!",
            icon="first_review.png",
            points_reward=50,
            action_type=ActionType.ORGANIZE_EVENT,
            required_count=1,
            is_cumulative=False
        ),

        # === ПЕРВЫЕ ДОСТИЖЕНИЯ ===

        Achievement(
            name="Первый отклик!",
            description="Спасибо за ваш первый вклад в поддержку актуальности карты",
            icon="first_status.png",
            points_reward=10,
            action_type=ActionType.SET_STATUS or ActionType.WRITE_REVIEW,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name='Первое приключение!',
            description="Поздравляем, вы посетили свою первую эко-точку, поделитесь впечатлениями?",
            icon="first_review.png",
            points_reward=20,
            action_type=ActionType.VISIT_OWN_TARA_POINT or ActionType.VISIT_RECYCLING_POINT,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name="Первый след!",
            description="Вы добавили свою первую эко-точку на карту",
            icon="first_point.png",
            points_reward=30,
            action_type=ActionType.ADD_POINT,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name='Начало дружбы!',
            description="Поздравляем, это было ваше первое мероприятие вместе с Экосистемой!",
            icon="first_review.png",
            points_reward=30,
            action_type=ActionType.PARTICIPATE_EVENT,
            required_count=1,
            is_cumulative=False
        ),
        Achievement(
            name='У этого города новый герой!',
            description="Вы организовали свое первое мероприятие и объединили силы горожан для общего блага!",
            icon="first_review.png",
            points_reward=50,
            action_type=ActionType.ORGANIZE_EVENT,
            required_count=1,
            is_cumulative=False
        ),

        # === НАКОПИТЕЛЬНЫЕ ДОСТИЖЕНИЯ ===

        Achievement(
            name="Человек высокого статуса!",
            description="Вы поставили 5 статусов, спасибо за активность!",
            badge_icon="badge_voice.png",
            points_reward=50,
            action_type=ActionType.SET_STATUS,
            required_count=20,
            is_cumulative=True
        ),
        Achievement(
            name="Кто отзывается, тот... для всех старается!",
            description="Вы оставили 5 отзывов на карте, спасибо за труд, коллега!",
            badge_icon="badge_review.png",
            points_reward=100,
            action_type=ActionType.WRITE_REVIEW,
            required_count=8,
            is_cumulative=True
        ),
        Achievement(
            name="Мы с Тамарой ходим с тарой!",
            description="Вы 5 раз посетили точки категории 'своя тара', так держать!",
            badge_icon="badge_zerowaste.png",
            points_reward=150,
            action_type=ActionType.VISIT_OWN_TARA_POINT,
            required_count=8,
            is_cumulative=True
        ),
        Achievement(
            name="Сдаёт сырьё, а не позиции!",
            description="Вы 5 раз посетили точки категории 'сдача сырья', сортировка – тяжелый труд, спасибо вам!",
            badge_icon="badge_cleaner.png",
            points_reward=200,
            action_type=ActionType.VISIT_RECYCLING_POINT,
            required_count=10,
            is_cumulative=True
        ),
        Achievement(
            name="Первопроходец Экосистемы!",
            description="Вы добавили 3 эко-точки на карту, благодарим настоящего знатока своего города!",
            badge_icon="badge_explorer.png",
            points_reward=150,
            action_type=ActionType.ADD_POINT,
            required_count=5,
            is_cumulative=True
        ),
        Achievement(
            name="Часть команды – часть Экосистемы!",
            description="Вы поучаствовали в 5 мероприятиях, город благодарен своему активному жителю!",
            badge_icon="badge_organizer.png",
            points_reward=200,
            action_type=ActionType.ORGANIZE_EVENT,
            required_count=2,
            is_cumulative=True
        ),
        Achievement(
            name="Прирождённый эко-лидер!",
            description="Вы организовали 3 мероприятия, Экосистема никогда не забудет ваш подвиг!",
            badge_icon="badge_organizer.png",
            points_reward=300,
            action_type=ActionType.ORGANIZE_EVENT,
            required_count=2,
            is_cumulative=True
        ),
    ]

    for ach in achievements:
        session.add(ach)

    await session.commit()
    print(f"✅ Создано {len(achievements)} достижений")
