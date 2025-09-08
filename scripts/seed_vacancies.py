from datetime import datetime

from app.database import SessionLocal
from app.models import Vacancy, VacancyStatus, User, UserRole


def main() -> None:
    session = SessionLocal()
    try:
        hr_user: User | None = (
            session.query(User).filter(User.role == UserRole.HR).order_by(User.id.asc()).first()
        )
        if not hr_user:
            print("ERR: No HR user found. Create an HR account first.")
            return

        vacancies: list[Vacancy] = []

        v1 = Vacancy(
            title="Senior Backend Engineer (Python/FastAPI, PostgreSQL, Async)",
            description=(
                "Мы ищем Senior Backend инженера, который поможет строить масштабируемые сервисы "
                "для HR‑платформы: высоконагруженные API, асинхронную обработку, интеграции с внешними AI/ML провайдерами. "
                "Вы будете влиять на архитектуру, качество кода и DX команды."
            ),
            requirements=(
                "— 4+ лет коммерческой разработки на Python\n"
                "— Отличные знания FastAPI, асинхронности (asyncio)\n"
                "— Опыт с PostgreSQL, SQLAlchemy, Alembic\n"
                "— Проектирование REST API, авторизация (JWT), CORS\n"
                "— Понимание очередей/фона (BackgroundTasks, job workers)\n"
                "— Будет плюсом: Redis/RabbitMQ, OpenAI/OpenRouter, Docker"
            ),
            salary_from=280000,
            salary_to=380000,
            location="Москва / удаленно",
            employment_type="full_time",
            experience_level="senior",
            benefits="Гибкий график, удаленка, ДМС, компенсация обучения, бюджет на конференции",
            company="VTB Mortech",
            status=VacancyStatus.OPEN,
            original_url="https://example.com/jobs/senior-backend-engineer",
            creator_id=hr_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        v2 = Vacancy(
            title="Middle Frontend Engineer (React/Next.js, TypeScript, UI/UX)",
            description=(
                "Ищем фронтенд‑разработчика, который поможет развивать web‑клиент HR‑платформы: "
                "Next.js app router, SSR/CSR, доступность и производительность. Много UI/UX, форм, оптимизаций "
                "и взаимодействий с API."
            ),
            requirements=(
                "— 2+ года с React/TypeScript\n"
                "— Опыт с Next.js (App Router), React Hooks\n"
                "— Знание TailwindCSS/Styled‑систем, адаптивной верстки\n"
                "— Работа с fetch/HTTP, обработкой ошибок, хранением токенов/куки\n"
                "— Будет плюсом: Zustand/Redux, Framer Motion, SWR/React Query"
            ),
            salary_from=180000,
            salary_to=260000,
            location="Санкт‑Петербург / удаленно",
            employment_type="full_time",
            experience_level="middle",
            benefits="Гибрид/удаленка, наставник, команда синьоров, оплата обучения и конференций",
            company="VTB Mortech",
            status=VacancyStatus.OPEN,
            original_url="https://example.com/jobs/middle-frontend-engineer",
            creator_id=hr_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        session.add_all([v1, v2])
        session.commit()
        print(f"OK: Created vacancies with ids: {v1.id}, {v2.id} (HR id: {hr_user.id})")
    finally:
        session.close()


if __name__ == "__main__":
    main()


