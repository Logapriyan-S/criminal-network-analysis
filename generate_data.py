"""
Generate synthetic criminal-network data for the prototype.

We deliberately plant structure the analytics should later discover:
  - 3 gangs (communities) that mostly talk within themselves
  - A "broker" who quietly links two gangs (low direct contacts, but
    high betweenness - the person centrality should surface as key)
  - A couple of pairs with no direct call but many shared contacts
    (targets for link prediction)

Because we control generation, we know the ground truth and can show
the model actually finding it.
"""

import json
import random

from faker import Faker

fake = Faker("en_IN")
random.seed(7)
Faker.seed(7)

N_PER_GANG = [9, 8, 7]          # three gangs
GANG_NAMES = ["Group Red", "Group Blue", "Group Green"]


def make_people():
    people = []
    pid = 1
    for gi, n in enumerate(N_PER_GANG):
        for _ in range(n):
            people.append({
                "id": f"P{pid:03d}",
                "name": fake.name(),
                "phone": fake.msisdn()[:10],
                "city": fake.city(),
                "gang": gi,          # ground-truth gang (hidden from analytics)
                "role": "member",
            })
            pid += 1
    # The broker - belongs nominally to gang 0 but bridges 0 and 1
    broker = {"id": f"P{pid:03d}", "name": fake.name(), "phone": fake.msisdn()[:10],
              "city": fake.city(), "gang": 0, "role": "broker"}
    people.append(broker)
    return people, broker["id"]


def make_edges(people, broker_id):
    by_gang = {0: [], 1: [], 2: []}
    for p in people:
        by_gang[p["gang"]].append(p["id"])

    edges = []

    def add(a, b, etype, weight):
        if a != b:
            edges.append({"source": a, "target": b, "type": etype, "weight": weight})

    # dense-ish calls WITHIN each gang
    for gang_members in by_gang.values():
        for a in gang_members:
            for b in gang_members:
                if a < b and random.random() < 0.45:
                    add(a, b, "call", random.randint(2, 20))

    # a few financial transactions within gangs
    for gang_members in by_gang.values():
        for _ in range(len(gang_members)):
            a, b = random.sample(gang_members, 2)
            add(a, b, "transaction", random.randint(1, 5))

    # broker links gang 0 and gang 1 with only a FEW calls each side
    for b in random.sample(by_gang[1], 3):
        add(broker_id, b, "call", random.randint(1, 3))
    for a in random.sample(by_gang[0], 2):
        add(a, broker_id, "call", random.randint(1, 3))

    # one faint cross-link between gang 1 and gang 2 (noise / weak tie)
    add(random.choice(by_gang[1]), random.choice(by_gang[2]), "call", 1)

    # shared-address edges (co-location) inside gangs - another signal type
    for gang_members in by_gang.values():
        if len(gang_members) >= 2:
            a, b = random.sample(gang_members, 2)
            add(a, b, "shared_address", 1)

    return edges


def main():
    people, broker_id = make_people()
    edges = make_edges(people, broker_id)

    data = {
        "people": people,
        "edges": edges,
        "ground_truth": {
            "broker": broker_id,
            "gangs": {p["id"]: p["gang"] for p in people},
            "gang_names": GANG_NAMES,
        },
    }
    with open("crime_data.json", "w") as f:
        json.dump(data, f, indent=2)

    print(f"Generated {len(people)} people and {len(edges)} connections.")
    print(f"Planted broker (should rank high on betweenness): {broker_id}")
    print("Saved to crime_data.json")


if __name__ == "__main__":
    main()
