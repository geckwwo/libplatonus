import aiohttp
from typing import Any, cast, Literal
from enum import Enum
from dataclasses import dataclass

@dataclass
class LessonTime:
    start_time: tuple[int, int]
    duration_minutes: int

    def full(self):
        starting = self.normalize(self.start_time)
        ending_x = list(self.start_time)

        ending_x[1] += self.duration_minutes
        while ending_x[1] >= 60:
            ending_x[0] += 1
            ending_x[1] -= 60
        
        ending = self.normalize(ending_x)
        return starting + " - " + ending

    @classmethod
    def normalize(cls, time: tuple[int, int] | list[int]):
        return ":".join(map(lambda x: str(x).rjust(2, "0"), time))

@dataclass
class Lesson:
    name: str
    teacher: str

    location: str
    building: str

    time: LessonTime

class RespondWith(Enum):
    Json = 1
    Raw = 2
    Nothing = 3

FitsJson = None | int | float | str | dict[str, 'FitsJson'] | list['FitsJson'] | bool

class PlatonusClient:
    def __init__(self, api_root: str, session: aiohttp.ClientSession):
        self.session = session
        self.api_root = api_root.rstrip("/")
        self.auth_token: str | None = None
        self.auth_sid: str | None = None

    async def post_endpoint(self, endpoint: str, data: dict[str, Any], auth: bool = False, respond_with: RespondWith = RespondWith.Json):
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        
        headers: dict[str, str] = {}
        if auth:
            assert self.auth_sid is not None
            assert self.auth_token is not None
            headers["sid"] = self.auth_sid
            headers["token"] = self.auth_token

        async with self.session.post(self.api_root + endpoint, json=data, headers=headers) as x:
            x.raise_for_status()
            match respond_with:
                case RespondWith.Json:
                    return cast(dict[str, Any], await x.json()), x.cookies
                case RespondWith.Raw:
                    return await x.text(), x.cookies
                case RespondWith.Nothing:
                    return None, x.cookies

    @classmethod
    async def from_credentials(cls, api_root: str, login: str, password: str):
        client = PlatonusClient(api_root, aiohttp.ClientSession())
        data, _ = await client.post_endpoint("/api/login", {
            "authForDeductedStudentsAndGraduates": "false", # why string, why??? platonus devs are retarded
            "icNumber": None,
            "iin": None,
            "login": login,
            "password": password
        })
        data = cast(dict[str, Any], data)

        assert data["login_status"] == "success"
        client.auth_token = data["auth_token"]
        client.auth_sid = data["sid"]
        
        return client #, data, cookies
    
    async def get_timetable(self, lang: Literal["en"] | Literal["ru"] | Literal["kz"] = "en"):
        # https://platonus.iitu.edu.kz/rest/schedule/userSchedule/student/initial/0/kz
        data, _ = await self.post_endpoint(f"/schedule/userSchedule/student/initial/0/{lang}", 
            {"studentTypeID":1,"statusID":1,"disciplineStudyLanguageIds":[1,2,3],"week":1}, auth=True)
        data = cast(dict[str, Any], data)
        
        hours_p = data["lessonHours"]
        hours: dict[str, LessonTime] = {}
        for hour in hours_p:
            hours[str(hour["number"])] = LessonTime(cast(tuple[int, int], tuple(map(int, hour["start"].split(":")[:2]))), int(hour["duration"]))
        timetable = data["timetable"]["days"]

        days: list[list[Lesson]] = [list() for _ in range(6)]
        for day_idx, day in timetable.items():
            day_idx = int(day_idx) - 1

            lessons = day["lessons"]
            for hour, data in lessons.items():
                if len(data["lessons"]) > 0:
                    time = hours[hour]
                    for i in data["lessons"]:
                        days[day_idx].append(Lesson(i["subjectName"], i["tutorName"], i["auditory"], i["building"], time))
        
        for day in days:
            day.sort(key=lambda x: int(x.time.normalize(x.time.start_time).replace(":", "")))

        return days

    async def close(self):
        await self.session.close()