import argparse, urllib, json
from datetime import datetime
from pymongo import MongoClient, GEOSPHERE
from pymongo.errors import (PyMongoError, BulkWriteError)
import generate_FoodList
import csv
import matplotlib.pyplot as plt
import time

client = MongoClient('localhost', 15986)
db = client['food_analysis']
filter_collection = db['pic_Info']
suburbs = db['suburbs']


def chooseArea(statistics, x):  # parameter is the statistics
    chosenArea = dict(sorted(statistics.items(), key=lambda item: sum(item[1].values()), reverse=True)[:x])
    return chosenArea


def chooseFood(suburb, x):  # parameter is the statistic[suburb]
    chosenFood = dict(sorted(suburb.items(), key=lambda item: item[1], reverse=True)[:x])
    return chosenFood


def determineFoodRange(foods, suburb):
    foods.update({'others': sum(suburb.values()) - sum(foods.values())})
    return foods


def draw_pie_chart(statistics, period):
    areas = chooseArea(statistics, 10)  # Choose Top X areas with most pictures to analyze
    for suburb in areas:
        plt.title(suburb + period)
        foods = chooseFood(statistics[suburb], 20)  # mewenti
        foodRange = determineFoodRange(foods, statistics[suburb])
        plt.pie([float(v) for v in foodRange.values()], labels=[k for k in foodRange.keys()],
                autopct='%1.1f%%')
        plt.show()
    return


def get_suburb(location):
    suburb_info = suburbs.find_one({"geometry": {"$geoIntersects": {"$geometry": location}}})
    suburb = 'None'
    if suburb_info:
        suburb = suburb_info['properties']['SA2_NAME16']
    return suburb


def suburb_statistics11():
    statistics = {}

    for item in filter_collection.find().limit(1000):
        classification = item['pic_pred']  # 以食物预测为分类依据
        location = item['pic_loc']  # 获取地点
        suburb = get_suburb(location)  # 获取地点所在area
        if suburb != 'None':  # 如果suburb不是空
            if suburb in statistics.keys():  # 如果有了这个suburb
                if classification in statistics[suburb].keys():  # 如果有了这个食物
                    statistics[suburb][classification] += 1  # foodCount += 1
                else:
                    statistics[suburb][classification] = 1  # foodCount = 1
            else:  # 如果这个suburb还没出现过
                statistics[suburb] = {}  # 建一个新的
                statistics[suburb][classification] = 1  # foodCount = 1
    return statistics


def getPeriodByTimestamp(timestamp):
    timePeriod = {'Breakfast': range(6, 9), 'Brunch': range(9, 11), 'Lunch': range(11, 15),
                  'Afternoon_Tea': range(15, 17), 'Dinner': range(17, 21),
                  'Late_Night_Supper': [21, 22, 23, 24, 1, 2, 3, 4, 5],
                  }
    st = time.localtime(timestamp)
    times = str(time.strftime('%Y-%m-%d %H:%M:%S', st))
    period = int(times.split(' ')[1].split(':')[0])
    for keys, values in timePeriod.items():
        if period in values:
            return keys


def suburb_statistics(timePoint):
    statistics = {}

    for item in filter_collection.find():
        classification = item['pic_pred']
        location = item['pic_loc']
        timestamp = item.get('pic_time')
        if timestamp is not None:
            period = getPeriodByTimestamp(timestamp)
            suburb = get_suburb(location)
            print(period)
            if period == timePoint and suburb != 'None':
                if suburb in statistics.keys():  # 如果有了这个suburb
                    if classification in statistics[suburb].keys():  # 如果有了这个食物
                        statistics[suburb][classification] += 1  # foodCount += 1
                    else:
                        statistics[suburb][classification] = 1  # foodCount = 1
                else:  # 如果这个suburb还没出现过
                    statistics[suburb] = {}  # 建一个新的
                    statistics[suburb][classification] = 1  # foodCount = 1
    return statistics


def nutritionFacts_analsis(statistics, foodInfo):
    result = {}

    for suburb in statistics:
        healthStar, protein, fat, carbohydrate, calorie, sodium, weighterTotal = 0, 0, 0, 0, 0, 0, 0
        foodDistribution = statistics[suburb]
        print(foodDistribution)
        foodCount = sum(statistics[suburb].values())
        for foods in foodDistribution:
            nutrition = foodInfo.get(foods)
            isMain = nutrition[7]
            weightedNum = foodDistribution[foods] if isMain == 0 else 4 * foodDistribution[foods]
            num = foodDistribution[foods]
            healthStar += 1 * float(nutrition[0]) * num if isMain == 0 else 4 * float(nutrition[0])
            protein += float(nutrition[2]) * num
            fat += float(nutrition[3]) * num
            carbohydrate += float(nutrition[4]) * num
            calorie += float(nutrition[5]) * num
            sodium += float(nutrition[6]) * num
            weighterTotal += weightedNum
        healthStar = round(healthStar / weighterTotal, 2)
        protein = round(protein / foodCount, 2)
        fat = round(fat / foodCount, 2)
        carbohydrate = round(carbohydrate / foodCount, 2)
        calorie = round(calorie / foodCount, 2)
        sodium = round(sodium / foodCount, 2)
        nutritionFacts = [healthStar, protein, fat, carbohydrate, calorie, sodium, foodCount]
        result[suburb] = nutritionFacts

    return result


def calculateavgMelb():
    healthStar, protein, fat, carbohydrate, calorie, sodium, num = 0, 0, 0, 0, 0, 0, 0
    result = {}

    csvreader = csv.reader(open('nutritionFacts.csv'))
    for row in csvreader:
        key = row[0]
        result[key] = list(row[1:])

    for keys in result:
        info = [float(element) for element in
                result[keys][0].replace(',', ' ').replace('[', ' ').replace(']', ' ').split()]
        healthStar += info[0] * info[6]
        protein += info[1] * info[6]
        fat += info[2] * info[6]
        carbohydrate += info[3] * info[6]
        calorie += info[4] * info[6]
        sodium += info[5] * info[6]
        num += info[6]
        print(info[6])

    result = [round(nutrition / num, 2) for nutrition in [healthStar, protein, fat, carbohydrate, calorie, sodium]]
    print(result)
    print(num)


def writeCSV(dict):
    with open('nutritionFacts.csv', 'w+') as csv_file:
        writer = csv.writer(csv_file)
        for key, value in dict.items():
            writer.writerow([key, value])


def preprocess_FoodInfo(foodInfo):
    csvreader = csv.reader(open('FoodInfo.csv'))
    result = {}
    firstLine = next(csvreader)
    for row in csvreader:
        key = row[0]
        result[key] = row[1:]
    return result


def analysis():
    # calculateavgMelb()

    foodInfo = preprocess_FoodInfo('FoodInfo.csv')
    # timePeriod = input("please choose a time period")
    statistics = suburb_statistics11()
    result = nutritionFacts_analsis(statistics, foodInfo)
    writeCSV(result)
    draw_pie_chart(statistics, timePeriod)


if __name__ == '__main__':
    analysis()
