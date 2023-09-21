import requests
import yaml


class rjapi:

    def __init__(self, config_file = None):
        if config_file is None:
            config_file = "config.yaml"
        self.config = self.__load_config(config_file)
        self.__search_endpoint = "https://brn-ybus-pubapi.sa.cz/restapi/routes/search/simple?departureDate={}&fromLocationId={}&toLocationId={}&fromLocationType={}&toLocationType={}&tariffs={}"
        self.__train_enpoint = "https://brn-ybus-pubapi.sa.cz/restapi/routes/{0}/simple?routeId={0}&fromStationId={1}&toStationId={2}&tariffs={3}"
        self.__shop_link = "https://regiojet.cz/?departureDate={}&fromLocationId={}&toLocationId={}&fromLocationType={}&toLocationType={}&tariffs={}"
    

    def __load_config(self, config_file):
        with open(config_file, "r") as f:
            cfg = yaml.safe_load(f)
        if type(cfg["tariff"]) is list:
            cfg["quantity"] = len(cfg["tariff"])
            cfg["tariff"] = "&tariffs=".join(cfg["tariff"])
        else:
            cfg["quantity"] = 1
        if type(cfg["preffered_class"]) is str:
            cfg["preffered_class"] = [cfg["preffered_class"]]
        return cfg
    

    def search_train(self, train):
        # Get all classes info for given train
        train_details = requests.get(self.__train_enpoint.format(train["id"], train["departureStationId"], train["arrivalStationId"], self.config["tariff"])).json()
        # Check max changes
        if len(train_details["sections"]) > self.config["max_changes"] + 1:
            return False
        # No preffered class
        if not self.config["preffered_class"]:
            return True
        # Find preffered class and check seat availability
        for i in train_details["priceClasses"]:
            if i["seatClassKey"] in self.config["preffered_class"] and i["freeSeatsCount"] >= self.config["quantity"]:
                return True
        return False


    def search_ticket(self):
        # Get all routes for given date
        day_trains = requests.get(self.__search_endpoint.format(self.config["date"], self.config["from"], self.config["to"], self.config["from_type"], self.config["to_type"], self.config["tariff"])).json()
        # No trains on given trains
        if "routes" not in day_trains:
            return False
        
        # Find trains with given time
        day_trains = day_trains["routes"]
        datetime = self.config["date"] + "T" + self.config["time"]
        trains = []
        for i in day_trains:
            if datetime in i["departureTime"]:
                trains.append(i)
        
        # No trains with given time
        if not trains:
            return False
        
        for train in trains:
            # Not enough tickets available or train not bookable
            if train["freeSeatsCount"] < self.config["quantity"] or not train["bookable"]:
                continue
        
            # Seat available - max changes exceeded or preffered class not available
            if not self.search_train(train):
                continue

            # Seat available
            return True
        
        # No train with seats available
        return False


    def send_alert(self):
        # Craft data
        data = {
            "message" : "Tickets for {}T{} available!".format(self.config["date"], self.config["time"]),
            "action" : self.__shop_link.format(self.config["date"], self.config["from"], self.config["to"], self.config["from_type"], self.config["to_type"], self.config["tariff"])
        }
        # Send to notify.run
        requests.post("https://notify.run/"+self.config["notify_code"], data=data)  