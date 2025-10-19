import asyncio
import json
from twscrape import API

async def main():
    api = API()
    
    with open("accounts.json",encoding="utf-8-sig") as f:
        accounts = json.load(f)

    for account in accounts:
        try:
            await api.pool.add_account(
                username=account["username"],
                password=account["password"],
                email=account["email"],
                email_password=account["email_pass"]
                )
            acc = await api.pool.get(account["username"])
            print(acc)
            result = await api.pool.login(acc)

            if result:
                print(f"Login Success: {account['username']}")
            else:
                print(f"Login Failed: {account['username']}")

        except Exception as e:
            print(f"ERROR processing {account['username']: (e)}")

if __name__ == "__main__":
    asyncio.run(main())
        