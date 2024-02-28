from curl_cffi import requests
from datetime import datetime, timedelta
import traceback
from rich.console import Console
from rich.theme import Theme
import os
from dotenv import load_dotenv
from prettytable import PrettyTable

custom_theme = Theme({"info": "dim cyan", "warning": "magenta", "danger": "bold red"})
console = Console(theme=custom_theme)
GREEN = "\033[92m"
RED = "\033[91m"
ENDC = "\033[0m"

load_dotenv()

headers = {
    "authority": "api.openloot.com",
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9",
    "content-type": "application/json",
    "cookie": os.getenv("COOKIE"),
    "origin": "https://openloot.com",
    "sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "X-Client-Id:": "marketplace",
    "X-Device-Id": os.getenv("X-DEVICE-ID"),
    "X-Is-Mobile": "false",
    "X-Session-Id": os.getenv("X-SESSION-ID"),
    "X-User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}

spawn_times = {
    ("rare", "small"): 72,
    ("rare", "medium"): 66,
    ("epic", "small"): 66,
    ("rare", "large"): 60,
    ("epic", "medium"): 60,
    ("legendary", "small"): 60,
    ("epic", "large"): 54,
    ("legendary", "medium"): 54,
    ("mythic", "small"): 54,
    ("legendary", "large"): 48,
    ("mythic", "medium"): 48,
    ("exalted", "small"): 48,
    ("mythic", "large"): 42,
    ("exalted", "medium"): 42,
    ("exalted", "large"): 36,
}


def calculate_time_difference(timestamp_str, spawn_time):
    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ")
    timestamp = timestamp + timedelta(hours=8)
    current_time = datetime.now()
    time_difference = current_time - timestamp
    remaining_time = timedelta(hours=spawn_time) - time_difference

    return remaining_time if remaining_time > timedelta(0) else timedelta(0)


def get_openloot_in_game_items(page=1, proxy=None, timeout=3):
    proxies = proxy if proxy else None
    url = f"https://api.openloot.com/v2/market/items/in-game?page={page}&pageSize=1000&sort=name%3Aasc&gameId=56a149cf-f146-487a-8a1c-58dc9ff3a15c&nftTags=NFT.SPACE"
    r = requests.get(
        url,
        proxies=proxies,
        headers=headers,
        impersonate="chrome120",
        timeout=timeout,
    )
    return r.json()


if __name__ == "__main__":
    os.system("cls")
    page = 1
    true_count = 0
    false_count = 0
    result = []
    while True:
        try:
            data = get_openloot_in_game_items(page)
            if "error" in data:
                print("错误: " + data["error"])
                input("按任意键继续")
                exit
            items = data["items"]
            for item in items:
                key = item["issuedId"]
                if item["extra"] == None or "attributes" not in item["extra"]:
                    continue
                for att in item["extra"]["attributes"]:
                    if att["name"] == "LastCrackedHourGlassDropTime":
                        timestamp = att["value"]
                        spawn_time = 72
                        item_tags = set(item["metadata"]["tags"])
                        for tags, time in spawn_times.items():
                            if set(tags).issubset(item_tags):
                                spawn_time = time
                                break
                        time_diff = calculate_time_difference(timestamp, spawn_time)
                        item["remaining_time"] = time_diff
                        result.append(item)

        except Exception as e:
            console.log(f"处理页面 {page} 时出现错误: {traceback.format_exc()}")
            continue
        page += 1
        if page > data["totalPages"]:
            break

    result.sort(key=lambda x: x["remaining_time"], reverse=True)
    table = PrettyTable()
    table.field_names = ["编号", "名称", "倒计时", "时间"]

    for item in result:
        time_diff = item["remaining_time"]
        id = item["issuedId"]
        name = item["metadata"]["name"]
        if time_diff <= timedelta(0):
            table.add_row([f"{GREEN}#{id:06d}{ENDC}", name, "", ""])
            true_count += 1
        else:
            table.add_row(
                [
                    f"{RED}#{id:06d}{ENDC}",
                    name,
                    time_diff,
                    (datetime.now() + time_diff).strftime("%Y-%m-%d %H:%M:%S"),
                ]
            )
            false_count += 1
    print(table)
    print(f"\n{GREEN}■ {true_count}{ENDC} {RED}■ {false_count}{ENDC}")
    print(f"最大刷新时间: {result[0]['remaining_time']}")
    print(f"最小刷新时间: {result[-1]['remaining_time']}")
    input("按任意键继续")
