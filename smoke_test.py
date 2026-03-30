from datetime import datetime

from app import app, load_config


def main():
    client = app.test_client()
    config = load_config()

    bootstrap = client.get("/api/bootstrap")
    assert bootstrap.status_code == 200, bootstrap.data

    suffix = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    email = f"prueba-{suffix}@correo.test"

    registration = client.post(
        "/api/register",
        json={"name": "Prueba Automatizada", "email": email},
    )
    assert registration.status_code == 200, registration.data

    selections = {
        office["id"]: office["candidates"][0]["id"]
        for office in config["offices"]
    }

    vote = client.post("/api/vote", json={"selections": selections})
    assert vote.status_code == 200, vote.data

    duplicate_vote = client.post("/api/vote", json={"selections": selections})
    assert duplicate_vote.status_code == 409, duplicate_vote.data

    results = client.get("/api/results")
    assert results.status_code == 200, results.data

    print("OK")


if __name__ == "__main__":
    main()
