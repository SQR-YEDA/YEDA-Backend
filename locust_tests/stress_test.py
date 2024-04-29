from locust import HttpUser, task, between


class OpenAPIUser(HttpUser):
    wait_time = between(1, 5)  # Wait time between simulated user actions
    headers: dict

    @task
    def login_user(self):
        payload = {
            "login": "string",
            "password": "string"
        }
        self.client.post("/login", json=payload, headers=self.headers)

    @task
    def get_elements(self):
        self.client.get("/elements", headers=self.headers)

    @task
    def get_user_tier_list(self):
        self.client.get("/tier-list", headers=self.headers)

    def on_start(self):
        # Perform login once at the start to get authentication token
        headers = {"Content-Type": "application/json"}
        payload = {
            "login": "string",
            "password": "string"
        }
        response = self.client.post("/login", json=payload, headers=headers)
        headers["Authorization"] = f"Bearer {response.json()['tokens']['access_token']}"
        self.headers = {"Authorization": f"Bearer {response.json()['tokens']['access_token']}"}
