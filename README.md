# Parking Rate Exercise


## Install:
``` 
pip install -r requirements.txt
```

## Running the code

### Start the service

```
# start up local server
python -m run 
```

### Endpoints
```
/load POST
    {
        "rates": [
            {
            "days": string - comma seperated string of days: "mon,tues,wed,thurs","fri","sat","sun"
            "times": string - interval in Unix time format %H%M-%H%M,
            "tz": string - entry from 2017c of the tz database
            "price": int
            },
        ]
    }
    
/query GET
    {
        "begin": string - ISO-8601 with timezones
        "end":  string - ISO-8601 with timezones
    }

```



### Making Requests

```
# load rates from json file (parking.json)
curl -i "http://127.0.0.1:5000/load" -X POST -H "Content-Type: application/json" -d @parking.json

# query service for parking rates
curl -i "http://127.0.0.1:5000/query" -X GET -H "Content-Type: application/json" -d '{"begin":"2015-07-01T07:00:00-05:00", "end":"2015-07-01T12:00:00-05:00"}'
curl -i "http://127.0.0.1:5000/query" -X GET -H "Content-Type: application/json" -d '{"begin":"2015-07-04T15:00:00+00:00", "end":"2015-07-04T20:00:00+00:00"}'
curl -i "http://127.0.0.1:5000/query" -X GET -H "Content-Type: application/json" -d '{"begin":"2015-07-04T07:00:00+05:00", "end":"2015-07-04T20:00:00+05:00"}'
```
