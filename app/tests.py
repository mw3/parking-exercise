import unittest
import datetime
from dateutil import tz
from app import parking

class TestParkingRateDataStore(unittest.TestCase):

    def test_add_parking_rate(self):
        d = parking.ParkingRateDataStore()
        for wd in range(0, 6):
            r = parking.ParkingRate(wd, 1, 2, wd)
            d.add_parking_rate(r)
            i = d.weekday_interval_trees[wd].all_intervals.pop()
            self.assertEqual(i.data, wd)

    def test_add_parking_rate(self):
        d = parking.ParkingRateDataStore()
        rates = [parking.ParkingRate(wd, 1, 2, wd) for wd in range(0,6)]
        d.add_parking_rates(rates)
        for r in rates:
            i = d.weekday_interval_trees[r.weekday].all_intervals.pop()
            self.assertEqual(i.data, r.weekday)

    def test_query_time_interval(self):
        d = parking.ParkingRateDataStore()
        rates = [
            parking.ParkingRate(3, (0, 1), (0, 2), 0),
            parking.ParkingRate(3, (0, 2), (0, 5), 1),
            parking.ParkingRate(3, (0, 5), (0, 8), 2),
        ]
        d.add_parking_rates(rates)
        r = d.query_time_interval((0, 3), (0, 4), 3)
        self.assertEqual(r, 1)

    def test_query_time_interval_no_result(self):
        d = parking.ParkingRateDataStore()
        rates = [
            parking.ParkingRate(3, (0, 1), (0, 2), 0),
            parking.ParkingRate(3, (0, 2), (0, 5), 1),
            parking.ParkingRate(3, (0, 8), (0, 9), 2),
        ]
        d.add_parking_rates(rates)
        r = d.query_time_interval((0, 6), (0, 7), 3)
        self.assertIsNone(r)

    def test_query_time_interval_offset(self):
        d = parking.ParkingRateDataStore()
        rates = [
            parking.ParkingRate(3, (0, 20), (1, 4), 10),
        ]
        d.add_parking_rates(rates)
        r = d.query_time_interval((0, 1), (0, 2), 3)
        self.assertEqual(r, 10)


class TestParkingRateDTO(unittest.TestCase):

    def test_add_parking_rate(self):
        r = parking.ParkingRate(3, 1, 2, 9000)
        self.assertEqual(r.weekday, 3)
        self.assertEqual(r.begin, 1)
        self.assertEqual(r.end, 2)
        self.assertEqual(r.rate, 9000)


class TestSpotHeroJsonParkingRateAdapter(unittest.TestCase):

    def test_get_weekdays_get_one(self):
        j = {'days': 'wed'}
        r = parking.SpotHeroJsonParkingRateAdapter().get_weekdays(j)
        self.assertEqual(r, [2])

    def test_get_weekdays_get_all(self):
        j = {'days': 'mon,tues,wed,thurs,fri,sat,sun'}
        r = parking.SpotHeroJsonParkingRateAdapter().get_weekdays(j)
        self.assertEqual(r, [0, 1, 2, 3, 4, 5, 6])

    def test_get_interval_time_objs(self):
        j = {'times': '0900-1115'}
        r = parking.SpotHeroJsonParkingRateAdapter().get_interval_time_objs(j)
        self.assertEqual(r[0], datetime.time(9, 0))
        self.assertEqual(r[1], datetime.time(11, 15))

    def test_get_utc_interval(self):
        begin_t, end_t = datetime.time(9, 0), datetime.time(11, 15)
        begin, end = parking.SpotHeroJsonParkingRateAdapter().get_utc_interval(begin_t, end_t, 'Etc/UTC')
        self.assertEqual(begin, (0, '0900'))
        self.assertEqual(end, (0, '1115'))

    def test_get_timezone(self):
        j = {'tz': 'America/Chicago'}
        r = parking.SpotHeroJsonParkingRateAdapter().get_timezone(j)
        self.assertEqual(r, 'America/Chicago')

    def test_get_rate(self):
        j = {'price': '1000'}
        r = parking.SpotHeroJsonParkingRateAdapter().get_rate(j)
        self.assertEqual(r, 1000)

    def test_process_rate_json(self):
        j = {
            'days': 'mon',
            'times': '0900-1115',
            'tz': 'Etc/UTC',
            'price': 1000,
        }
        r = parking.SpotHeroJsonParkingRateAdapter().process_rate_json(j)[0]
        self.assertEqual(r.weekday, 0)
        self.assertEqual(r.begin, (0, '0900'))
        self.assertEqual(r.end, (0, '1115'))
        self.assertEqual(r.rate, 1000)


class TestRelativeUtcUtil(unittest.TestCase):

    def test_parse_datetime_str(self):
        r = parking.RelativeUtcUtil.parse_datetime_str("2015-07-01T07:00:00-05:00")
        self.assertEqual(r, datetime.datetime(2015, 7, 1, 7, 00, 00, tzinfo=tz.tzoffset(None, -5*60*60)))

    def test_get_relative_utc_interval(self):
        dt = datetime.datetime(2015, 7, 1, 7, 00, 00, tzinfo=tz.tzoffset(None, -5*60*60))
        r = parking.RelativeUtcUtil.get_relative_utc_interval(dt, dt)
        self.assertEqual(r, ((0, '1200'), (0, '1200')))

    def test_get_relative_utc_interval_plus_zero(self):
        dt1 = datetime.datetime(2015, 7, 1, 7, 00, 00, tzinfo=tz.tzoffset(None, -5*60*60))
        dt2 = datetime.datetime(2015, 7, 1, 17, 00, 00, tzinfo=tz.tzoffset(None, -5*60*60))
        r = parking.RelativeUtcUtil.get_relative_utc_interval(dt1, dt2)
        self.assertEqual(r, ((0, '1200'), (0, '2200')))

    def test_get_relative_utc_interval_plus_one(self):
        dt1 = datetime.datetime(2015, 7, 1, 7, 00, 00, tzinfo=tz.tzoffset(None, -5*60*60))
        dt2 = datetime.datetime(2015, 7, 1, 20, 00, 00, tzinfo=tz.tzoffset(None, -5*60*60))
        r = parking.RelativeUtcUtil.get_relative_utc_interval(dt1, dt2)
        self.assertEqual(r, ((0, '1200'), (1, '0100')))

    def test_get_relative_interval_plus_zero(self):
        dt1 = datetime.datetime(2015, 7, 1, 7, 00, 00, tzinfo=tz.tzoffset(None, -5*60*60))
        dt2 = datetime.datetime(2015, 7, 1, 17, 00, 00, tzinfo=tz.tzoffset(None, -5*60*60))
        r = parking.RelativeUtcUtil.get_relative_interval(dt1, dt2)
        self.assertEqual(r, ((0, '0700'), (0, '1700')))

    def test_get_relative_interval_plus_one(self):
        dt1 = datetime.datetime(2015, 7, 1, 7, 00, 00, tzinfo=tz.tzoffset(None, -5*60*60))
        dt2 = datetime.datetime(2015, 7, 2, 20, 00, 00, tzinfo=tz.tzoffset(None, -5*60*60))
        r = parking.RelativeUtcUtil.get_relative_interval(dt1, dt2)
        self.assertEqual(r, ((0, '0700'), (1, '2000')))


if __name__ == '__main__':
    unittest.main()
