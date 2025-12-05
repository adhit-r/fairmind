import requests

def create_user():
    url = "http://localhost:8000/api/v1/auth/register"
    payload = {
        "email": "dev@fairmind.ai",
        "password": "dev",
        "full_name": "Developer"
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("User created successfully!")
            print(f"Email: {payload['email']}")
            print(f"Password: {payload['password']}")
        elif response.status_code == 400 and "already exists" in response.text:
            print("User already exists.")
        else:
            print(f"Failed to create user: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_user()
