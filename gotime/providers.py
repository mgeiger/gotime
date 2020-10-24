import time

import requests


class Location:
    def __init__(self, address, latitude, longitude):
        self._latitude = latitude
        self._longitude = longitude
        self._address = address

    @property
    def latitude(self):
        return self._latitude

    @property
    def longitude(self):
        return self._longitude

    @property
    def address(self):
        return self._address


class Result:
    def __init__(self, provider=None, distance=None, duration=None, steps=None, fuel_used=None):
        self.provider = provider
        self.distance = distance
        self.duration = duration
        self.steps = steps
        self.fuel_used = fuel_used

    def __str__(self):
        s = f"<{self.__class__.__name__}> {self.provider}: distance={self.distance}, duration={self.duration}"
        if self.steps:
            s += f", steps={self.steps}"
        if self.fuel_used:
            s += f", fuel_used={self.fuel_used}"
        return s


class Provider:
    def get_result(self, start, end):
        raise NotImplementedError


class AzureMaps(Provider):
    name = "azure"

    def __init__(self, primary, secondary):
        self.primary = primary
        self.secondary = secondary

    def _request_data(self, start: Location, end: Location):
        url = "https://atlas.microsoft.com/route/directions/json?"
        url += "api-version=1.0"
        url += "&travelMode=car"
        url += "&traffic=true"
        url += "&subscription-key={}".format(self.primary)
        url += "&query={},{}:{},{}".format(
            start.latitude, start.longitude,
            end.latitude, end.longitude)
        r = requests.get(url)
        self._last_json = r.json()

    def _parse_data(self, data: dict=None):
        if data is None:
            data = self._last_json

        summary = data['routes'][0]['summary']
        distance = summary['lengthInMeters'] / 1000.0
        duration = summary['travelTimeInSeconds']
        self._last_result = Result(
            provider=self.name,
            distance=distance,
            duration=duration
        )

    def get_result(self, start: Location, end: Location) -> Result:
        self._request_data(start, end)
        self._parse_data()
        return self._last_result

    def __str__(self):
        return f"<{self.__class__.__bases__[0].__name__}> {self.name}: {self.primary[:6]}, {self.secondary[:6]}"


class BingMaps(Provider):
    name = "bing"

    def __init__(self, key):
        self.key = key
        self._last_result = None
        self._last_json = None

    def _request_data(self, start: Location, end: Location):
        url = 'http://dev.virtualearth.net/REST/V1/Routes/Driving?wp.0={origin}&wp.1={destination}&key={key}'
        url = url.format(
            key=self.key,
            origin=start.address,
            destination=end.address
        )
        r = requests.get(url)
        self._last_json = r.json()

    def _parse_data(self, data: dict=None):
        if data is None:
            data = self._last_json
        resource = data['resourceSets'][0]['resources'][0]

        steps = len(resource['routeLegs'][0]['itineraryItems'])
        duration = resource['travelDuration']
        distance = resource['travelDistance']
        self._last_result = Result(
            provider=self.name,
            distance=distance,
            duration=duration,
            steps=steps
        )

    def get_result(self, start: Location, end: Location) -> Result:
        self._request_data(start, end)
        self._parse_data()
        return self._last_result

    def __str__(self):
        return f"<{self.__class__.__bases__[0].__name__}> {self.name}: {self.key[:6]}"


class GoogleMaps(Provider):
    name = "google"

    def __init__(self, key):
        self.key = key
        self._last_result = None
        self._last_json = None

    def _request_data(self, start: Location, end: Location):
        model = "best_guess"
        now_secs = str(int(time.time()))
        url = 'https://maps.googleapis.com/maps/api/directions/json?'
        url += 'origin={origin}&destination={destination}'
        url += '&key={key}&mode=driving&traffic_model={model}'
        url += '&departure_time={now_secs}'
        url = url.format(
            origin=f"{start.latitude},{start.longitude}",
            destination=f"{end.latitude},{end.longitude}",
            key=self.key,
            model=model,
            now_secs=now_secs)
        r = requests.get(url)
        self._last_json = r.json()

    def _parse_data(self, data: dict=None):
        if data is None:
            data = self._last_json
        legs = data['routes'][0]['legs']
        duration = legs[0]["duration_in_traffic"]["value"]
        distance = legs[0]["distance"]["value"] / 1000.0
        steps = len(legs[0]['steps'])
        self._last_result = Result(
            provider=self.name,
            distance=distance,
            duration=duration,
            steps=steps
        )

    def get_result(self, start: Location, end: Location) -> Result:
        self._request_data(start, end)
        self._parse_data()
        return self._last_result

    def __str__(self):
        return f"<{self.__class__.__bases__[0].__name__}> {self.name}: {self.key[:6]}"


class HereMaps(Provider):
    name = "here"

    def __init__(self, primary: str, secondary: str):
        """
        :param primary: App ID
        :param secondary: App Code
        """
        self.primary = primary
        self.secondary = secondary
        self._last_result = None
        self._last_json = None

    def _request_data(self, start: Location, end: Location):
        url = 'https://route.cit.api.here.com/routing/7.2/calculateroute.json'
        url += '?app_id={}'.format(self.primary)  # app_id
        url += '&app_code={}'.format(self.secondary)  # app_code
        url += '&waypoint0=geo!{},{}'.format(start.latitude, start.longitude)
        url += '&waypoint1=geo!{},{}'.format(end.latitude, end.longitude)
        url += '&mode=fastest;car'
        r = requests.get(url)
        self._last_json = r.json()

    def _parse_data(self, data: dict=None):
        if data is None:
            data = self._last_json
        summary = data['response']['route'][0]['summary']
        distance = summary['distance'] / 1000.0
        duration = summary['trafficTime']
        self._last_result = Result(
            provider=self.name,
            distance=distance,
            duration=duration
        )

    def get_result(self, start: Location, end: Location) -> Result:
        self._request_data(start, end)
        self._parse_data()
        return self._last_result

    def __str__(self):
        return f"<{self.__class__.__bases__[0].__name__}> {self.name}: {self.primary[:6]}, {self.secondary[:6]}"


class MapBoxMaps(Provider):
    """
    Directions API: https://docs.mapbox.com/api/navigation/#directions
    """
    name = "mapbox"

    def __init__(self, key: str):
        self.key = key
        self._last_result = None
        self._last_json = None

    def _request_data(self, start: Location, end: Location):
        profile = 'mapbox/driving-traffic'
        url = "https://api.mapbox.com/directions/v5/{}/{}%2C{}%3B{}%2C{}.json?access_token={}".format(
            profile, start.longitude, start.latitude,
            end.longitude, end.latitude, self.key)
        r = requests.get(url)
        self._last_json = r.json()

    def _parse_data(self, data: dict=None):
        if data is None:
            data = self._last_json
        route = data['routes'][0]
        distance = route['distance'] / 1000.0
        duration = route['duration']

        self._last_result = Result(
            provider=self.name,
            distance=distance,
            duration=duration)

    def get_result(self, start: Location, end: Location) -> Result:
        self._request_data(start, end)
        self._parse_data()
        return self._last_result

    def __str__(self):
        return f"<{self.__class__.__bases__[0].__name__}> {self.name}: {self.key[:6]}"


class MapQuestMaps(Provider):
    """
    Directions API: https://developer.mapquest.com/documentation/directions-api/
    """
    name = "mapquest"

    def __init__(self, key: str):
        self.key = key
        self._last_json = None
        self._last_result = None

    def _request_data(self, start: Location, end: Location):
        origin = "{}%2C{}".format(start.latitude, start.longitude)
        destination = "{}%2C{}".format(end.latitude, end.longitude)
        url = f'https://www.mapquestapi.com/directions/v2/route?key={self.key}&from={origin}&to={destination}'
        # N.B. we request in KM
        url += f'&doReverseGeocode=false&routeType=fastest&unit=k'
        r = requests.get(url)
        self._last_json = r.json()

    def _parse_data(self, data: dict=None):
        if data is None:
            data = self._last_json
        route = data['route']
        distance = route['distance']
        duration = route['realTime']
        fuel_used = route['fuelUsed']
        steps = len(route['legs'][0]['maneuvers'])
        self._last_result = Result(provider=self.name, distance=distance,
                                   duration=duration, steps=steps,
                                   fuel_used=fuel_used)

    def get_result(self, start: Location, end: Location) -> Result:
        self._request_data(start, end)
        self._parse_data()
        return self._last_result

    def __str__(self):
        return f"<{self.__class__.__bases__[0].__name__}> {self.name}: key={self.key[:6]}"


class TomTomMaps(Provider):
    name = "tomtom"

    def __init__(self, key: str):
        self.key = key
        self._last_result = None
        self._last_json = None

    def _request_data(self, start: Location, end: Location):
        url = "https://api.tomtom.com/routing/1/calculateRoute/{},{}:{},{}/json?avoid=unpavedRoads&key={}".format(
            start.latitude, start.longitude,
            end.latitude, end.longitude, self.key)
        r = requests.get(url)
        self._last_json = r.json()

    def _parse_data(self, data: dict=None):
        if data is None:
            data = self._last_json
        summary = data['routes'][0]['summary']
        # TODO: What is the storage data units?
        duration = summary['travelTimeInSeconds']
        distance = summary['lengthInMeters'] / 1000.0
        self._last_result = Result(provider=self.name,
                                   distance=distance,
                                   duration=duration)

    def get_result(self, start: Location, end: Location):
        self._request_data(start, end)
        self._parse_data()
        return self._last_result

    def __str__(self):
        return f"<{self.__class__.__bases__[0].__name__}> {self.name}: key={self.key[:6]}"
