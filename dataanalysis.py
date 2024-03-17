import json

import matplotlib.pyplot as plt
import seaborn as sns

import pyspark

from pyspark.sql import SparkSession
from pyspark.sql import types
from pyspark.sql import functions as F


spark = SparkSession.builder.appName('Athena').getOrCreate()

file_path = '\craigslist_vehicles.csv'

df_cars = spark.read.options(header=True, inferSchema=True, delimiter=',', multiLine=True).csv(file_path)

df_cars.printSchema()


drop_cols = ['url', 'region_url', 'image_url', 'description']

df_cars = df_cars.drop(*drop_cols)

# both null values and null indicators(other) exist, set the indicator to null (to prevent confusion)

df_cars = df_cars.replace('other', None, subset=['cylinders'])


# both null values and null indicators(missing) exist, set the indicator to null (to prevent confusion)

df_cars = df_cars.replace('missing', None, subset=['title_status'])


# Latitude should be between (-90, 90), otherwise set null

df_cars = df_cars.withColumn('lat', F.when(F.col('lat').rlike('^-?\d+\.?\d+$'), F.col('lat')))
df_cars = df_cars.withColumn('lat', F.col('lat').cast(types.FloatType()))

df_cars = df_cars.withColumn('lat', F.when((-90 <= F.col('lat')) & (F.col('lat') <= 90), F.col('lat')))
# Longitude should be between (-180, 180), otherwise set null

df_cars = df_cars.withColumn('long', F.when(F.col('long').rlike('^-?\d+\.?\d+$'), F.col('long')))
df_cars = df_cars.withColumn('long', F.col('long').cast(types.FloatType()))
df_cars = df_cars.withColumn('long', F.when((-180 <= F.col('long')) & (F.col('long') <= 180), F.col('long')))
# Posting date should be in format yyyy-MM-dd HH:mm:ss.SSSS

df_cars = df_cars.withColumn('posting_date', F.when(F.col('posting_date').rlike('^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}-\d{4}$'), F.col('posting_date')))
df_cars = df_cars.withColumn('posting_date', F.col('posting_date').cast(types.TimestampType()))

df_cars.select('price', 'year', 'odometer', 'lat', 'long').summary().show()

# date column to year and month columns

df_cars = df_cars.withColumn('posting_year', F.year(F.col('posting_date')))
df_cars = df_cars.withColumn('posting_month', F.month(F.col('posting_date')))

df_cars = df_cars.drop('posting_date')

df_cars.select('price', 'year', 'odometer', 'lat', 'long').summary().show()

df_cars.createOrReplaceTempView('cardata')

#histo gram

df_result = spark.sql('SELECT manufacturer, price FROM cardata WHERE manufacturer IN ("chevrolet", "ford", "toyota")')
df_result = df_result.toPandas()
                                                                                
fig, ax = plt.subplots(1, 1, figsize=(8, 4))

_ = sns.histplot(data=df_result, x='price', hue='manufacturer', binwidth=0.2, ax=ax)

plt.show()

df_result = spark.sql('SELECT condition, odometer, price FROM cardata')
df_result = df_result.toPandas()
                                                                                
fig, ax = plt.subplots(1, 1, figsize=(6, 6))

_ = sns.scatterplot(data=df_result, x='odometer', y='price', hue='condition', ax=ax, s=1)

#scatterplot

plt.show()

#pie chart

df_result = spark.sql('SELECT condition FROM cardata')
df_result = df_result.toPandas()
                                                                                
fig, ax = plt.subplots(1, 1, figsize=(6, 6))


data = df_result['condition'].value_counts().nlargest(4)
colors = sns.color_palette('pastel')

plt.pie(data.values, labels=data.index, colors=colors, autopct='%.0f%%')
plt.show()

