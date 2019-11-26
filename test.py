import datetime

def parse_datetime(str_date):
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.datetime.strptime(str_date, fmt)
        except ValueError:
            pass

date = "2019-11-21 00:00:00.22"
# p_date = datetime.datetime.strftime(date, '%Y-%m-%d %H:%M:%S').date()
print(parse_datetime(date))


