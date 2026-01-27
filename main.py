import asyncio
import json
from libplatonus import PlatonusClient

dayNames = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб"]

async def main():
    with open(".credentials") as f:
        login, password = json.load(f)
    client = await PlatonusClient.from_credentials("https://platonus.iitu.edu.kz/rest/", login, password)
    timetable = await client.get_timetable(lang="ru")

    for day, dayName in zip(timetable, dayNames):
        print(f"{dayName}:")
        if len(day) == 0:
            print("\t (no lessons)")
        else:
            for lesson in day:
                print(f"\t {lesson.name} ({lesson.building}, {lesson.location}) - {lesson.time.full()}")

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
