import requests
import yaml


class rjapi:

    def __init__(self, config_file = None):
        if config_file is None:
            config_file = "config.yaml"
        self.config = self.__load_config(config_file)
        self.__search_endpoint = "https://brn-ybus-pubapi.sa.cz/restapi/routes/search/simple?locale=sk&departureDate={}&fromLocationId={}&toLocationId={}&fromLocationType=CITY&toLocationType=CITY&tariffs=REGULAR"
        self.__train_enpoint = "https://brn-ybus-pubapi.sa.cz/restapi/routes/{0}/simple?routeId={0}&fromStationId={1}&toStationId={2}&tariffs=REGULAR"
        self.__shop_link = "https://regiojet.cz/?departureDate={}&fromLocationId={}&toLocationId={}&fromLocationType=CITY&toLocationType=CITY&tariffs={}"
    

    def __load_config(self, config_file):
        with open(config_file, "r") as f:
            cfg = yaml.safe_load(f)
        if type(cfg["tariff"]) is str:
            cfg["tariff"] = [cfg["tariff"]]
        cfg["quantity"] = len(cfg["tariff"])
        return cfg
    

    def search_class(self, train):
        # Get all classes info for given train
        classes = requests.get(self.__train_enpoint.format(train["id"], train["departureStationId"], train["arrivalStationId"])).json()
        # Find preffered class and check availability
        for i in classes["priceClasses"]:
            if i["seatClassKey"] == self.config["preffered_class"] and i["freeSeatsCount"] >= self.config["quantity"]:
                return True
        return False


    def search_ticket(self):
        # Get all routes for given date
        trains = requests.get(self.__search_endpoint.format(self.config["date"], self.config["from"], self.config["to"])).json()
        # No trains on given trains
        if "routes" not in trains:
            return False
        
        # Find train with given time
        trains = trains["routes"]
        datetime = self.config["date"] + "T" + self.config["time"]
        train = None
        for i in trains:
            if datetime in i["departureTime"]:
                train = i
                break
        
        # No train with given time
        if train is None:
            return False
        
        # No tickets available
        if not train["freeSeatsCount"]:
            return False
        
        # Seat available and no preffered class
        if not self.config["preffered_class"]:
            return True
        
        # Seat available but preffered class,
        # check that class availability
        return self.search_class(train)


    def send_alert(self):
        # Craft data
        tariffs = "&tariffs=".join(self.config["tariff"])
        data = {
            "message" : "Tickets for {}T{} available!".format(self.config["date"], self.config["time"]),
            "action" : self.__shop_link.format(self.config["date"], self.config["from"], self.config["to"], tariffs)
        }
        # Send to notify.run
        requests.post("https://notify.run/"+self.config["notify_code"], data=data)