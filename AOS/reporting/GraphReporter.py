import matplotlib.pyplot as plt
from AOS.database import db

start = 20019
x, y, fy = [], [], []

data = db.get_all(db.REPORTED_VERSIONS)

print(data)

print("Loading the graph data, press Control + C to load the webserver.")

def daily_usage_graph():
    x, y = [], []

    for day in data:
        try:
            z = day["data"]["live"]
        except KeyError:
            continue

        x.append(int(day["administer_id"]) - start)
        y.append(day["data"]["live"])

    y2 = [item.get('1.2', 0) for item in y]
    y3 = [item.get('1.2.1', 0) for item in y]
    y4 = [item.get('1.2.2', 0) for item in y]
    y5 = [item.get('1.2.3', 0) for item in y]
    y6 = [item.get('2.0', 0) for item in y]
    y = [item.get('1.1.1', 0) for item in y]

    plt.plot(x, y, marker='o')
    plt.plot(x, y2, marker='*')
    plt.plot(x, y3, marker='o')
    plt.plot(x, y4, marker='o')
    plt.plot(x, y5, marker='o')
    plt.plot(x, y6, marker='o')

    # Add labels and title
    plt.ylabel("Place Starts")
    plt.xlabel("Day (Unix time)")
    plt.title("Administer usage over the LIVE branch")
    plt.legend(["1.1.1", "1.2", "1.2.1", "1.2.2", "1.2.3", "2.0"])

def overall_places():
    x = []
    y = []

    for day in data:
        db_key: str = day["administer_id"]
        if db_key.startswith("day-"):
            day_number = int(db_key.split("-")[1]) - start
            places_len = day["data"].get("places_len", 0)

            x.append(day_number)
            y.append(places_len)

    plt.plot(x, y, marker='o', label="Overall Places")

    plt.ylabel("Places")
    plt.xlabel("Day")
    plt.title("Number of Administer-powered games over time")
    plt.legend()

def combined():
    x, y = [], []
    for day in data:
        try:
            z = day["data"]["live"]
        except KeyError:
            continue

        x.append(int(day["administer_id"]) - start)
        y.append(day["data"]["live"])

    y2 = [item.get('1.2', 0) for item in y]
    y3 = [item.get('1.2.1', 0) for item in y]
    y4 = [item.get('1.2.2', 0) for item in y]
    y5 = [item.get('1.2.3', 0) for item in y]
    y6 = [item.get('2.0', 0) for item in y]
    y = [item.get('1.1.1', 0) for item in y]

    plt.plot(x, y, marker='o', label="1.1.1")
    plt.plot(x, y2, marker='o', label="1.2")
    plt.plot(x, y3, marker='o', label="1.2.1")
    plt.plot(x, y4, marker='o', label="1.2.2")
    plt.plot(x, y5, marker='o', label="1.2.3")
    plt.plot(x, y6, marker='o', label="2.0")

    x, y = [], []

    for day in data:
        db_key: str = day["administer_id"]
        if db_key.startswith("day-"):
            day_number = int(db_key.split("-")[1]) - start
            places_len = day["data"].get("places_len", 0)

            x.append(day_number)
            y.append(places_len)

    plt.plot(x, y, marker='*', label="Overall Places")
    plt.xlabel("Day (missing some data)")
    plt.ylabel("Total Places")

    plt.legend()

#daily_usage_graph()
#overall_places()
combined()

plt.tight_layout()
plt.savefig("/home/Pyx/adm/Log")

plt.show()
