import datetime
import os
import pickle
import tempfile

from dateutil import tz, parser
from intervaltree import IntervalTree, interval


class ParkingRateDataStore:

    def __init__(self):
        self.weekday_interval_trees = (
            IntervalTree(), IntervalTree(), IntervalTree(), IntervalTree(),
            IntervalTree(), IntervalTree(), IntervalTree()
        )

    def add_parking_rates(self, parking_rates):
        for pr in parking_rates:
            self.add_parking_rate(pr)

    def add_parking_rate(self, parking_rate):
        self.weekday_interval_trees[parking_rate.weekday].addi(
            parking_rate.begin, parking_rate.end, parking_rate.rate
        )

    def query_time_interval(self, begin, end, weekday):
        results = self.weekday_interval_trees[weekday].overlap(begin, end)
        if not results:
            results, begin, end = self.query_offset(begin, end, weekday)
        if results:
            query_interval = interval.Interval(begin, end)
            result = results.pop()  # we don't have overlapping rates
            if result.contains_interval(query_interval):
                return result.data
            else:
                return None
        else:
            return None

    def query_offset(self, begin, end, weekday):
        if begin[0] == 0 and end[0] == 0:
            new_begin, new_end = (1, begin[1]), (1, end[1])
            return self.weekday_interval_trees[weekday].overlap(new_begin, new_end), new_begin, new_end
        else:
            return None, begin, end


    @staticmethod
    def path():
        return os.path.join(tempfile.gettempdir(), 'ParkingRateDataStore')

    def persist(self):
        with open(self.path(), 'wb') as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls):
        with open(cls.path(), 'rb') as f:
            return pickle.load(f)


class ParkingRate:

    def __init__(self, weekday, begin, end, rate):
        """
        :param weekday: int
            0-6: Monday-Sunday
        :param begin: tuple
            0: int
                -1 to 1 day offset for time
            1: str
                UTC (%H%M)
        :param end: tuple
            0: int
                -1 to 1 day offset for time
            1: str
                UTC (%H%M)
        :param rate: int
            US cents
        """
        self.weekday = weekday
        self.begin = begin
        self.end = end
        self.rate = rate


class ParkingRateAdapter:

    def process(self, data):
        pass


class SpotHeroJsonParkingRateAdapter(ParkingRateAdapter):

    WEEKDAY_MAP = {
        'mon':      0,
        'tues':     1,
        'wed':      2,
        'thurs':    3,
        'fri':      4,
        'sat':      5,
        'sun':      6
    }

    def process(self, rate_json):
        rates_json = rate_json['rates']  # assuming valid input
        rates = list()
        for rj in rates_json:
            rates.extend(self.process_rate_json(rj))
        return rates

    def process_rate_json(self, rate_json):
        weekdays = self.get_weekdays(rate_json)
        begin_time_obj, end_time_obj = self.get_interval_time_objs(rate_json)
        timezone = self.get_timezone(rate_json)
        begin_utc, end_utc = self.get_utc_interval(begin_time_obj, end_time_obj, timezone)
        rate = self.get_rate(rate_json)
        return [ParkingRate(wd, begin_utc, end_utc, rate) for wd in weekdays]

    def get_weekdays(self, rate_json):
        return [self.WEEKDAY_MAP[d] for d in rate_json['days'].split(',')]

    @staticmethod
    def get_utc_interval(begin, end, timezone_str):
        this_tz = tz.gettz(timezone_str)
        begin = RelativeUtcUtil.get_datetime_from_time_obj(begin, this_tz)
        end = RelativeUtcUtil.get_datetime_from_time_obj(end, this_tz)
        return RelativeUtcUtil.get_relative_utc_interval(begin, end)

    def get_interval_time_objs(self, rate_json):
        begin, end = rate_json['times'].split('-')
        return self.get_time_obj(begin), self.get_time_obj(end)

    @staticmethod
    def get_timezone(rate_json):
        return rate_json['tz']

    @staticmethod
    def get_time_obj(time_str):
        return datetime.datetime.strptime(time_str, '%H%M').time()

    @staticmethod
    def get_rate(rate_json):
        return int(rate_json['price'])


class RelativeUtcUtil:

    @classmethod
    def parse_datetime_str(cls, datetime_str):
        return parser.parse(datetime_str)

    @classmethod
    def get_relative_utc_interval(cls, begin, end):
        begin_utc = begin.astimezone(tz.UTC)
        end_utc = end.astimezone(tz.UTC)
        return cls.get_relative_interval(begin_utc, end_utc)

    @classmethod
    def get_relative_interval(cls, begin, end):
        """
        Supports maximum one day interval
        """
        offset = cls.get_day_offset(begin, end)
        begin_str = begin.strftime('%H%M')
        end_str = end.strftime('%H%M')

        if offset == 0:
            return (0, begin_str), (0, end_str)
        elif offset == 1:
            return (0, begin_str), (1, end_str)
        else:
            raise NotImplementedError

    @staticmethod
    def get_datetime_from_time_obj(time_obj, this_tz, basis_datetime=None):
        basis_datetime = basis_datetime or datetime.date.today()  # Daylight savings depends on date
        datetime_obj = datetime.datetime.combine(basis_datetime, time_obj).replace(tzinfo=this_tz)
        return datetime_obj

    @staticmethod
    def get_day_offset(begin, end):
        return (end.date() - begin.date()).days


def query_mgr(begin_str, end_str):
    parking_datastore = ParkingRateDataStore.load()
    begin = RelativeUtcUtil.parse_datetime_str(begin_str)
    end = RelativeUtcUtil.parse_datetime_str(end_str)
    if begin.date() != end.date():
        return 'unavailable'
    weekday = begin.weekday()
    begin, end = RelativeUtcUtil.get_relative_utc_interval(begin, end)
    result = parking_datastore.query_time_interval(begin, end, weekday)
    return result or 'unavailable'


def load_mgr(rates_json):
    shjson_adapter = SpotHeroJsonParkingRateAdapter()
    rates = shjson_adapter.process(rates_json)
    new_datastore = ParkingRateDataStore()
    new_datastore.add_parking_rates(rates)
    new_datastore.persist()
