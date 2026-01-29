import tkinter
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from skibidiplatonus.storage import SimpleJSONStorage
from libplatonus import PlatonusClient

dayNames = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб"]

async def main():
    storage = SimpleJSONStorage(".credentials.json")
    client: PlatonusClient | None = None

    root = tkinter.Tk()
    root.title("SkibidiPlatonus")
    root.geometry("640x480")

    if "authdata" not in storage.storage:
        r = tkinter.Toplevel(root)
        r.title("Log in")
        r.geometry("320x240")
        root.withdraw()

        tkinter.Label(r, text="API root:").pack()
        api_root_entry = tkinter.Entry(r)
        api_root_entry.pack()
        tkinter.Label(r, text="Username:").pack()
        username_entry = tkinter.Entry(r)
        username_entry.pack()
        tkinter.Label(r, text="Password:").pack()
        password_entry = tkinter.Entry(r, show="*")
        password_entry.pack()

        async def log_in():
            nonlocal client
            client = await PlatonusClient.from_credentials(api_root_entry.get(),
                                                     username_entry.get(),
                                                     password_entry.get())
            storage.storage["authdata"] = {
                "api_root": api_root_entry.get(),
                "token": client.auth_token,
                "sid": client.auth_sid
            }
            storage.save()
            r.destroy()  # Close the login window
            root.deiconify()  # Show the main window
        tkinter.Button(r, text="Log in", command=lambda: (asyncio.get_event_loop().create_task(log_in()), None)[1]).pack()

        # wait for the login window to close
        r.wait_window()
    else:
        authdata = storage.storage["authdata"]
        client = PlatonusClient.from_authdata(authdata["api_root"], authdata["token"], authdata["sid"])
    assert client is not None

    timetable = await client.get_timetable("en")
    # show the timetable in the main window
    # table with column for each week day
    for day_id, day in enumerate(timetable):
        day_frame = tkinter.Frame(root)
        day_frame.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=True)
        tkinter.Label(day_frame, text=dayNames[day_id]).pack()
        for lesson in day:
            lesson_frame = tkinter.Frame(day_frame, borderwidth=1, relief="solid")
            lesson_frame.pack(fill=tkinter.X, padx=5, pady=5)
            tkinter.Label(lesson_frame, text=f"{lesson.time.full()} - {lesson.name}").pack()
            tkinter.Label(lesson_frame, text=f"Location: {lesson.building}, {lesson.location}").pack()
            tkinter.Label(lesson_frame, text=f"Instructor: {lesson.teacher}").pack()

    root.mainloop()

if __name__ == "__main__":
    asyncio.run(main())