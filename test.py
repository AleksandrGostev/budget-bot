import datetime

date = "2019-11-21 00:00:00.22"
p_date = datetime.datetime.strftime(date, '%Y-%m-%d %H:%M:%S').date()
print(p_date)