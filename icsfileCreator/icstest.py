from ics import Calendar
import requests

url = "https://urlab.be/events/urlab.ics"
c = Calendar(requests.get(url).text)

print(c)

# print(c.events)