import requests
import time


class BaseMapsApi(object):
    def __init__(self):
        pass

    def format_data(self, key, origin, destination, model=None, now_secs=None):
        data = {'key': key,
                'origin': origin.replace(' ', '+'),
                'destination': destination.replace(' ', '+')}
        if model is not None:
            data['model'] = model
        if now_secs is not None:
            data['now_secs'] = now_secs
        return data


class GoogleMapsApi(BaseMapsApi):
    config_name = 'google'
    # See here for API info:
    # https://developers.google.com/maps/documentation/directions/intro#traffic-model
    url = 'https://maps.googleapis.com/maps/api/directions/json?'
    url += 'origin={origin}&destination={destination}'
    url += '&key={key}&mode=driving&traffic_model={model}'
    url += '&departure_time={now_secs}'

    def __init__(self, key=None):
        super().__init__()
        if key is None:
            self.key = 'UNKNOWN'
        else:
            self.key = key

    def query(self, origin, destination):
        now_secs = str(int(time.time()))
        data = self.format_data(self.key, origin, destination,
                                TrafficModel.BEST, now_secs)
        r = requests.get(self.url.format(**data))
        if r.status_code != 200:
            return None, None
        legs = r.json()['routes'][0]['legs'][0]
        duration_in_traffic = legs['duration_in_traffic']['value']
        seconds = int(duration_in_traffic)
        steps = len(r.json()['routes'][0]['legs'][0]['steps'])
        return seconds, steps

    def get_type(self):
        return self.config_name


class TrafficModel:
    """
    Enum-like class showing the Google Traffic model
    """
    BEST = "best_guess"
