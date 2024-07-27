import requests
import json
import time
from colorama import Fore, Style, init
from json import JSONDecodeError  # Import JSONDecodeError from the json module

# Initialize Colorama
init(autoreset=True)

# Read Auth Tokens from TXT file
def read_auth_tokens_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        auth_tokens = [line.strip() for line in file.readlines()]
    return auth_tokens

# Read Coin Limit values from config.json file
def read_config_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        config = json.load(file)
    return config

# Create headers for the requests
def create_headers(auth_token):
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
        "Origin": "https://ranch.kuroro.com",
        "Priority": "u=1, i",
        "Referer": "https://ranch.kuroro.com/",
        "Sec-Ch-Ua": "\"Chromium\";v=\"124\", \"Google Chrome\";v=\"124\", \"Not-A.Brand\";v=\"99\"",
        "Sec-Ch-Ua-Mobile": "?1",
        "Sec-Ch-Ua-Platform": "\"Android\"",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
    }
    return headers

def get_daily_streak_state(headers):
    url = "https://ranch-api.kuroro.com/api/DailyStreak/GetState"
    response = requests.get(url, headers=headers)
    return response

def claim_daily_bonus(headers):
    url = "https://ranch-api.kuroro.com/api/DailyStreak/ClaimDailyBonus"
    response = requests.post(url, headers=headers)
    return response

def perform_farming_and_feeding(headers, mine_amount, feed_amount):
    url = "https://ranch-api.kuroro.com/api/Clicks/MiningAndFeeding"
    data = {
        "mineAmount": mine_amount,
        "feedAmount": feed_amount
    }
    response = requests.post(url, headers=headers, json=data)
    return response

def get_purchasable_upgrades(headers):
    url = "https://ranch-api.kuroro.com/api/Upgrades/GetPurchasableUpgrades"
    response = requests.get(url, headers=headers)
    return response

def buy_upgrade(headers, upgrade_id):
    url = "https://ranch-api.kuroro.com/api/Upgrades/BuyUpgrade"
    data = {"upgradeId": upgrade_id}
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print(Fore.GREEN + f"Successfully bought upgrade with upgradeId: {upgrade_id}")
    else:
        print(Fore.RED + f"Failed to buy upgrade with upgradeId: {upgrade_id}")
    return response

def process_account(auth_token, coin_limit, account_number):
    print(Fore.CYAN + f"\n---------------- Login to account {account_number} ----------------")
    headers = create_headers(auth_token)
    
    state_response = get_daily_streak_state(headers)
    if state_response.status_code == 200:
        state_data = state_response.json()
        if not state_data['isTodayClaimed']:
            print(Fore.GREEN + "Logged in successfully! You have not received the reward today.")
            claim_response = claim_daily_bonus(headers)
            if claim_response.status_code == 200:
                claim_data = claim_response.json()
                print(Fore.GREEN + f"{claim_data['message']}")
            else:
                print(Fore.RED + "Reward already claimed today")
        else:
            print(Fore.GREEN + "Logged in successfully! You have received the reward today.")
        
        mine_amount = 100
        feed_amount = 100
        farm_response = perform_farming_and_feeding(headers, mine_amount, feed_amount)
        if farm_response.status_code == 200:
            try:
                farm_data = farm_response.json()
                print(Fore.GREEN + f"Farm and feed successful: {farm_data}")
            except JSONDecodeError:  # Handle JSON decoding errors
                print(Fore.YELLOW + "Farm and feed successful but did not receive JSON feedback.")
                print(Fore.YELLOW + f"Response text: {farm_response.text}")  # Log the response text
        elif farm_response.status_code == 500:
            print(Fore.YELLOW + "The energy is not enough to farm and feed the pet.")
            upgrades_response = get_purchasable_upgrades(headers)
            if upgrades_response.status_code == 200:
                upgrades_data = upgrades_response.json()
                upgrades_purchased = False
                print(Fore.BLUE + "Purchasable upgrades:")
                for upgrade in upgrades_data:
                    if upgrade["canBePurchased"] and upgrade["cost"] < coin_limit:
                        print(Fore.BLUE + f"Buying upgrade: {upgrade['name']} for {upgrade['cost']} coins")
                        buy_response = buy_upgrade(headers, upgrade["upgradeId"])
                        if buy_response.status_code == 200:
                            print(Fore.GREEN + f"Successfully bought {upgrade['name']} for {upgrade['cost']} coins, earning {upgrade['earnIncrement']} per hour")
                            upgrades_purchased = True
                        else:
                            print(Fore.RED + f"Failed to buy upgrade {upgrade['name']}")
                if not upgrades_purchased:
                    print(Fore.YELLOW + f"No upgrades available for less than {coin_limit} coins.")
            else:
                print(Fore.RED + "Cannot get list of purchasable upgrades")
        else:
            print(Fore.RED + "Farm and feed failed")
            print(Fore.RED + f"Response content: {farm_response.text}")
    else:
        print(Fore.RED + "Login failed")

def main():
    auth_tokens = read_auth_tokens_from_file('data.txt')
    config = read_config_from_file('config.json')
    coin_limit = config.get("coin_limit", 5)
    
    while True:
        for idx, auth_token in enumerate(auth_tokens):
            process_account(auth_token, coin_limit, idx + 1)
        
        for i in range(10, 0, -1):
            print(Fore.MAGENTA + f"\r============ Complete, wait {i} second(s)... ============", end="")
            time.sleep(1)
        print(Fore.MAGENTA + "\n====================================================")

if __name__ == "__main__":
    main()
