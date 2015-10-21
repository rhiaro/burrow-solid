import requests
import datetime
import pytz
from pytz import timezone
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS
from rdflib.namespace import XSD
from urllib2 import HTTPError

LDP = Namespace('http://www.w3.org/ns/ldp#')
DC = Namespace('http://purl.org/dc/terms/')
AS2 = Namespace('http://www.w3.org/ns/activitystreams#')
BLOG = Namespace('http://vocab.amy.so/blog#')

def load(url):
  g = Graph()
  try:
    g.load(url)
  except HTTPError, e:
    if e.code == 401:
      print "Access denied"
    else:
      print e.code
    return False
  
  return g

def list_checkins():
  res = load("https://data.amy.gy/locations/")
  checkins = []
  if res:
    for s,p,o in res.triples((None, LDP.contains, None)):
      checkins.append(o)
    return checkins

def load_checkins():
  checkins = list_checkins()
  g = Graph()
  for checkin in checkins:
    data = load(checkin)
    for s,p,o in data:
      g.add((s,p,o))
  return g

def locations_graph():
  g = Graph()
  g.load("locations.ttl", format="turtle")
  return g

def post_checkin(location, tz="EST", date=None):
  if not date:
    tzobj = pytz.timezone(tz)
    dt = datetime.datetime.now(tzobj)
    date = dt.strftime("%Y-%m-%dT%H:%M:%S%z")
  
  locations = locations_graph()
  loc_uri = locations.value(predicate=DC.title, object=Literal(location))
  g = Graph()
  g.add( (URIRef(""), AS2.location, URIRef(loc_uri)) )
  g.add( (URIRef(""), DC.created, Literal(date, datatype=XSD.dateTime)) )

  headers = {"Content-Type": "text/turtle", "Link": "<http://www.w3.org/ns/ldp#Resource; rel=\"type\""}
  data = g.serialize(format="turtle")
  r = requests.post("https://data.amy.gy/locations/", headers=headers, data=data, verify=False)
  print r.status_code
  return r

def main():
  data = load_checkins()
  locations = locations_graph()

  s = set(data.subjects())  
  for uri in s:
    time = data.value(uri, DC.created)
    location = data.value(uri, AS2.location)
    label = locations.value(location, BLOG.pastLabel)
    print "%s at %s" % (label, time)

  print "\n\n"

  print post_checkin("transit")


if __name__ == '__main__':
  main()