import re
import yaml
import time
import datetime
import calendar

with open("config.yaml", "rb") as f:
    config = yaml.full_load(f)

def execution_time(f):
    def wrapper(*args, **kwargs):
        start =  time.time()
        f(*args, **kwargs)
        print(f"Execution time: {time.time() - start}")
    return wrapper
        
def valid(elements: dict) -> bool:
    valid_m = [str(i) for i in range(60)] + ["*"]
    valid_h = [str(i) for i in range(24)] + ["*"] 
    valid_dom = [str(i) for i in range(1, 32, 1)] + ["*"]
    valid_mon = [str(i) for i in range(1, 13, 1)] + ["*"]
    valid_dow = [str(i) for i in range(7)] + ["*"]

    if elements["m"] not in valid_m:
        raise ValueError("Minutes invalid")
    if elements["h"] not in valid_h:
        raise ValueError("Hours invalid")
    if elements["dom"] not in valid_dom:
        raise ValueError("Day of month invalid")
    if elements["mon"] not in valid_mon:
        raise ValueError("Month invalid")
    if elements["dow"] not in valid_dow:
        raise ValueError("Day of week invalid")

def convert_to_string(elements: str):
    temp = []
    result = ""
    for key, value in elements.items():
        if value == "*":
            temp.append("*")
            continue
        if key == "m":
            temp.append(value)
        if key == "h":
            temp.append(value)
        if key == "dom":
            temp.append(value)
        if key == "mon":
            temp.append(config["month"][int(value)-1])
        if key == "dow":
            temp.append(config["date"]["crontab_rule"][int(value)])
    
    if temp[0] == "*":
        result += "At every minute "
        if temp[1] != "*":                                                                           
            result += f"past hour {temp[1]} "
    else:
        if temp[1] == "*":
            result += f"At minute {temp[0]} "
        else:
            result += f"At {temp[1]}:{temp[0]} "

    if temp[2] != "*":
        result += f"on day-of-month {temp[2]} "
    if temp[4] != "*":
        result += f"on {temp[4]} "
    if temp[3] != "*":
        result += f"in {temp[3]} "
    
    return temp, result

def first_dow(year, month, dow):
  day = ((8+dow) - datetime.datetime(year, month,1).weekday())%7
  if day == 0:
    day += 7

  while True:
    try:
      yield datetime.datetime(year, month, day)
      day += 7
    except ValueError:
      break

def get_next_day(list_elements: list, today):
    dom, mon, dow = list_elements[2:]
    temp = []
    if dom == "*" and mon == "*" and dow == "*":
        return [today + datetime.timedelta(days=i) for i in range(5)]
    if dom == "*" and mon != "*" and dow == "*":
        mon = config["string2month"][mon]
        temp = [datetime.datetime(today.year, mon, i) for i in range(1, calendar.monthrange(today.year, mon)[1] + 1)]
        temp = filter(lambda x : x > today or x.date() == today.date(), temp)
        return sorted(list(set(temp)))[:5]
        
    if mon == "*":
        if dow != "*":
            dow = config["date"]["datetime_rule"][dow]
            for i in range(today.month, 13):
                temp.extend(first_dow(today.year, i, dow))
        if dom != "*":
            for i in range(today.month, 13):
                temp.append(datetime.datetime(today.year, i, int(dom)))
        temp = list(filter(lambda x : x > today or x.date() == today.date(), temp))
        temp =  sorted(list(set(temp)))[:5]
        return temp
    else:
        mon = config["string2month"][mon]
        if dow != "*":
            dow = config["date"]["datetime_rule"][dow]
            temp.extend(first_dow(today.year, mon, dow))
        if dom != "*":
            temp.append(datetime.datetime(today.year, mon, int(dom)))
        temp = list(filter(lambda x : x > today or x.date() == today.date(), temp))
        temp = sorted(list(set(temp)))[:5]
        return temp

def get_next_datetime(elements):
    today = datetime.datetime.now()
    today_copy = today
    date_result = []
    list_next_datetime = []

    while True:
        list_next_day = get_next_day(elements, today_copy)
        if list_next_day:
           date_result.extend(list_next_day)
        if len(date_result) < 5:
            today_copy = today_copy.replace(today_copy.year + 1, 1, 1)
        else:
            break
            
    if elements[0] != "*" and elements[1] != "*":
        for index, d in enumerate(date_result[:5]):
            d = d.strftime('%Y-%m-%d')
            t = datetime.time(hour=int(elements[1]), minute=int(elements[0])).strftime("%H:%M:%S")
            text = "Next" if index == 0 else "Then"
            list_next_datetime.append(f"{d} {t}")

    if elements[0] == "*" and elements[1] != "*":
        counter = 0
        if date_result[0].date() == today.date():
            if today.hour == int(elements[1]):
                d = date_result[0].strftime('%Y-%m-%d')
                for i in range(today.minute +1, 60):
                    if counter < 5:
                        counter += 1
                        t = datetime.time(hour=int(elements[1]), minute=i).strftime("%H:%M:%S")
                        list_next_datetime.append(f"{d} {t}")

                if counter < 5:
                    d = date_result[1].strftime('%Y-%m-%d')
                    for i in range(0, 60):
                        counter += 1
                        t = datetime.time(hour=int(elements[1]), minute=i).strftime("%H:%M:%S")
                        list_next_datetime.append(f"{d} {t}")
                        if counter == 5:
                            break

            elif today.hour > int(elements[1]):
                d = date_result[1].strftime('%Y-%m-%d')
                for i in range(5):
                    t = datetime.time(hour=int(elements[1]), minute=i).strftime("%H:%M:%S")
                    list_next_datetime.append(f"{d} {t}")
            else:
                d = date_result[0].strftime('%Y-%m-%d')
                for i in range(5):
                    t = datetime.time(hour=int(elements[1]), minute=i).strftime("%H:%M:%S")
                    list_next_datetime.append(f"{d} {t}")
        else:
            d = date_result[0].strftime('%Y-%m-%d')
            for i in range(5):
                t = datetime.time(hour=int(elements[1]), minute=i).strftime("%H:%M:%S")
                list_next_datetime.append(f"{d} {t}")


    if elements[0] != "*" and elements[1] == "*":
        if date_result[0].date() == today.date():
            if today.minute >= int(elements[0]):
                d = date_result[0].strftime('%Y-%m-%d')
                for i in range(today.hour + 1, 24):
                    t = datetime.time(hour=i, minute=int(elements[0])).strftime("%H:%M:%S")
                    list_next_datetime.append(f"{d} {t}")

                if 24 - (today.hour +1) < 5:
                    d = date_result[1].strftime('%Y-%m-%d')
                    for i in range(5 + (today.hour + 1) - 24):
                        t = datetime.time(hour=i, minute=int(elements[0])).strftime("%H:%M:%S")
                        list_next_datetime.append(f"{d} {t}")

            else:
                d = date_result[0].strftime('%Y-%m-%d')
                for i in range(today.hour, 24):
                    t = datetime.time(hour=i, minute=int(elements[0])).strftime("%H:%M:%S")
                    list_next_datetime.append(f"{d} {t}")

                if 24 - today.hour < 5:
                    d = date_result[1].strftime('%Y-%m-%d')
                    for i in range(5+today.hour -24):
                        t = datetime.time(hour=i, minute=int(elements[0])).strftime("%H:%M:%S")
                        list_next_datetime.append(f"{d} {t}")

        else:
            d = date_result[0].strftime('%Y-%m-%d')
            for i in range(5):
                t = datetime.time(hour=i, minute=int(elements[0])).strftime("%H:%M:%S")
                list_next_datetime.append(f"{d} {t}")
    return list_next_datetime

# @execution_time  
def parse_result(crontab: str) -> str:
    crontab = re.sub(" +", " ", crontab)
    crontab = crontab.strip()
    if len(crontab.split(" ")) != 5:
        raise ValueError("Missing value")
        
    elements = ["m", "h", "dom", "mon", "dow"]
    elements = {k:v for k, v in zip(elements, crontab.split(" "))}
    valid(elements)
    temp, string_result = convert_to_string(elements)
    print(string_result)
    list_next_datetime = get_next_datetime(temp)
    for index, i in enumerate(list_next_datetime):
        text = "Next" if index == 0 else "Then"
        print(text + " at " + i)

print(parse_result("2 * 1 2 3"))