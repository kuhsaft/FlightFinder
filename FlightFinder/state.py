import re
from enum import Enum
from sqlite3 import Connection


class State:
    """
    Stores the state for the main application
    """
    _distance_regex = r"(\d+) to (\d+)"

    def __init__(self, db_conn: Connection):
        self.db_conn = db_conn

        self.group_by = GroupBy.month
        self.order_by = OrderBy.seats_transported

        self.airports = self.get_airports()
        self.airport_options = ['Any'] + [x[1] for x in self.airports]

        self.origin = '%'
        self.dest = '%'

        self.distance_options = ['Any'] + \
                                ['{} to {}'.format(x, x + 99) for x in range(0, 500, 100)] + \
                                ['{} to {}'.format(x, x + 499) for x in range(500, 6000, 500)]
        self.distance = 'Any'

    def get_origin_airport_code(self):
        """
        Gets the origin airport code selected
        :returns: the airport code or '%' when not found
        """
        airport = '%'
        for a in self.airports:
            if self.origin == a[1]:
                airport = a[0]

        return airport

    def get_destination_airport_code(self):
        """
        Gets the destination airport code selected
        :returns: the airport code or '%' when not found
        """
        airport = '%'
        for a in self.airports:
            if self.dest == a[1]:
                airport = a[0]

        return airport

    def get_distance_filter(self):
        """
        Gets the distance filter minimum and maximum selected
        :returns: a dictionary with keys 'min' and 'max'
        """
        matches = re.findall(State._distance_regex, self.distance, re.MULTILINE)
        if len(matches) == 0:
            return {'min': 0, 'max': 10000}
        else:
            match = matches[0]
            return {'min': int(match[0]), 'max': int(match[1])}

    def get_query_params(self):
        """
        Gets all the query parameters
        :return: a dictionary of the query parameters
        """
        return {
            'group_by': self.group_by.name,
            'order_by': self.order_by.name,
            'distance_filter': self.get_distance_filter(),
            'origin': self.get_origin_airport_code(),
            'destination': self.get_destination_airport_code(),
        }

    def get_results(self):
        """
        Performs a query
        :return: a list of tuples of (month, carrier, seats_transported, open_seats)
        """
        query_params = self.get_query_params()
        query = '''
            SELECT
              m.name                                                                                  AS month,
              carrier_name                                                                            AS airline,
              -- seats delivered = (%% flights performed) * seats
              SUM(CAST(seats * CAST(departures_performed AS REAL) / departures_scheduled AS INTEGER)) AS seats_transported,
              -- open seats = seats - passengers
              SUM(seats - passengers)                                                                 AS open_seats
            FROM
              flights
              JOIN
              months m ON flights.month_number = m.number
            WHERE
              service_class_code = 'F'
              AND departures_scheduled >= departures_performed
              AND distance BETWEEN ? AND ?
              AND origin_code LIKE ?
              AND dest_code LIKE ?
            GROUP BY %s
            ORDER BY %s
              DESC;
        ''' % (query_params['group_by'], query_params['order_by'])
        return self.db_conn.execute(query, (
            query_params['distance_filter']['min'],
            query_params['distance_filter']['max'],
            query_params['origin'],
            query_params['destination'],
        )).fetchall()

    def get_airports(self):
        """
        Gets all airports that are in the results query
        :return: a list of tuples of (airport_code, label)
        """
        return self.db_conn.execute('''
          SELECT DISTINCT a.code, printf('%s (%s)', a.code, a.description)
          FROM flights
          JOIN airports a ON flights.origin_code = a.code OR flights.dest_code = a.code
          WHERE
            service_class_code = 'F'
            AND departures_scheduled >= departures_performed
            AND passengers != 0
          ORDER BY a.code ASC
        ''').fetchall()


class GroupBy(Enum):
    month = 0
    carrier_name = 1


class OrderBy(Enum):
    seats_transported = 0
    open_seats = 1
